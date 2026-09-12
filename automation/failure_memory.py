"""Build and query a gated, rebuildable SQLite FTS5 failure-memory index."""

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import sys


FAILURE_RECORDS_SCRIPT = Path(__file__).resolve().with_name("failure_records.py")
FAILURE_RECORDS_SPEC = importlib.util.spec_from_file_location(
    "bima_failure_memory_records", FAILURE_RECORDS_SCRIPT)
if FAILURE_RECORDS_SPEC is None or FAILURE_RECORDS_SPEC.loader is None:
    raise RuntimeError("cannot load the reviewed failure-record contract")
failure_records = importlib.util.module_from_spec(FAILURE_RECORDS_SPEC)
FAILURE_RECORDS_SPEC.loader.exec_module(failure_records)


MINIMUM_REAL_CASES = 100
SYNC_PATH_MARKERS = {"onedrive", "dropbox", "googledrive", "google drive", "iclouddrive", "syncthing"}


class FailureMemoryError(ValueError):
    """Failure-memory storage or retrieval violates its contract."""


def _outside_synchronized_storage(path, repository_root):
    path = path.resolve()
    repository_root = repository_root.resolve()
    if path == repository_root or path.is_relative_to(repository_root):
        raise FailureMemoryError("database must remain outside the repository")
    if str(path).startswith("\\\\"):
        raise FailureMemoryError("database cannot use a network path")
    lowered = {part.lower() for part in path.parts}
    if lowered & SYNC_PATH_MARKERS:
        raise FailureMemoryError("database cannot use synchronized storage")
    parent = path.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
        raise FailureMemoryError("database parent cannot be a link or junction")
    return path


def readiness(record_set, minimum_real_cases=MINIMUM_REAL_CASES):
    if minimum_real_cases < MINIMUM_REAL_CASES:
        raise FailureMemoryError("production readiness threshold cannot be below 100")
    summary = failure_records.summarize(record_set)
    ready = summary["real_verified_records"] >= minimum_real_cases
    return {
        "schema": "bima-failure-memory-report.v1",
        "status": "READY" if ready else "BLOCKED",
        "reason_code": "CORPUS_GATE_SATISFIED" if ready else "INSUFFICIENT_REAL_CASES",
        "dataset_id": summary["dataset_id"],
        "record_set_sha256": summary["record_set_sha256"],
        "minimum_real_cases": minimum_real_cases,
        "real_verified_records": summary["real_verified_records"],
        "total_records": summary["total_records"],
        "indexed_active_records": 0,
        "database_created": False,
    }


def _connect(path):
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = DELETE")
    connection.execute("PRAGMA synchronous = FULL")
    return connection


def _searchable(record):
    return "\n".join([
        record["failure"]["reason_code"],
        record["cause"]["summary"],
        record["fix"]["summary"],
        record["scope"]["command_ref"],
        record["scope"]["rule_version"],
        *record["scope"]["repositories"],
    ])


def build_index(record_set, database_path, repository_root,
                minimum_real_cases=MINIMUM_REAL_CASES):
    failure_records.validate_record_set(record_set)
    report = readiness(record_set, minimum_real_cases)
    database_path = _outside_synchronized_storage(database_path, repository_root)
    if report["status"] != "READY":
        return report
    if database_path.exists():
        raise FailureMemoryError("database target already exists; use a new rebuild path")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    building = database_path.with_name(database_path.name + ".building")
    if building.exists():
        raise FailureMemoryError("stale build target exists")
    connection = None
    try:
        connection = _connect(building)
        if not any("ENABLE_FTS5" in row[0] for row in connection.execute("PRAGMA compile_options")):
            raise FailureMemoryError("SQLite runtime does not provide FTS5")
        connection.executescript("""
            BEGIN IMMEDIATE;
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE records (
                id TEXT PRIMARY KEY,
                record_json TEXT NOT NULL,
                status TEXT NOT NULL,
                case_kind TEXT NOT NULL,
                scope_kind TEXT NOT NULL,
                project_id TEXT,
                classification TEXT NOT NULL,
                allowed_projects_json TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE records_fts USING fts5(record_id UNINDEXED, searchable);
            PRAGMA user_version = 1;
        """)
        canonical_set = failure_records.canonical_bytes(record_set)
        metadata = {
            "dataset_id": record_set["dataset_id"],
            "record_set_sha256": report["record_set_sha256"],
            "record_set_json": canonical_set.decode("utf-8"),
            "schema": "bima-failure-memory.v1",
        }
        connection.executemany(
            "INSERT INTO metadata(key, value) VALUES (?, ?)", sorted(metadata.items()))
        indexed = 0
        for record in record_set["records"]:
            record_json = failure_records.canonical_bytes(record).decode("utf-8").rstrip("\n")
            connection.execute(
                "INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record["id"], record_json, record["status"], record["case_kind"],
                    record["scope"]["kind"], record["scope"]["project_id"],
                    record["access"]["classification"],
                    json.dumps(record["access"]["allowed_projects"], separators=(",", ":")),
                ),
            )
            if record["status"] == "ACTIVE":
                connection.execute(
                    "INSERT INTO records_fts(record_id, searchable) VALUES (?, ?)",
                    (record["id"], _searchable(record)),
                )
                indexed += 1
        connection.commit()
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise FailureMemoryError("SQLite integrity check failed")
        connection.close()
        connection = None
        building.replace(database_path)
        report["indexed_active_records"] = indexed
        report["database_created"] = True
        return report
    except (FailureMemoryError, sqlite3.Error, OSError):
        if connection is not None:
            connection.close()
        raise


def export_record_set(database_path):
    if not database_path.is_file():
        raise FailureMemoryError("database is missing")
    connection = sqlite3.connect(f"file:{database_path.resolve()}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'record_set_json'").fetchone()
        if row is None:
            raise FailureMemoryError("database lacks portable source records")
        record_set = failure_records.strict_json(row[0].encode("utf-8"))
        failure_records.validate_record_set(record_set)
        digest = connection.execute(
            "SELECT value FROM metadata WHERE key = 'record_set_sha256'").fetchone()
        if digest is None or failure_records.summarize(record_set)["record_set_sha256"] != digest[0]:
            raise FailureMemoryError("database source digest is inconsistent")
        return record_set
    finally:
        connection.close()


def _fts_query(query):
    if not isinstance(query, str) or not query or len(query) > 512:
        raise FailureMemoryError("query is invalid")
    tokens = re.findall(r"[A-Za-z0-9_.-]+", query)[:12]
    if not tokens:
        raise FailureMemoryError("query has no searchable tokens")
    return " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens)


def _accessible(row, project_id):
    classification, scope_kind, record_project, allowed_json = row
    allowed = json.loads(allowed_json)
    if classification == "public":
        return True
    if classification == "restricted":
        return project_id in allowed
    if scope_kind == "project" and record_project == project_id:
        return True
    return project_id in allowed


def search(database_path, query, project_id, limit=10):
    if not isinstance(project_id, str) or not project_id or not 1 <= limit <= 50:
        raise FailureMemoryError("search scope or limit is invalid")
    connection = sqlite3.connect(f"file:{database_path.resolve()}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            """
            SELECT r.id, r.record_json, r.classification, r.scope_kind,
                   r.project_id, r.allowed_projects_json, bm25(records_fts)
            FROM records_fts JOIN records r ON r.id = records_fts.record_id
            WHERE records_fts MATCH ?
            ORDER BY bm25(records_fts), r.id
            LIMIT 200
            """,
            (_fts_query(query),),
        ).fetchall()
    except sqlite3.Error as exc:
        raise FailureMemoryError("FTS query failed") from exc
    finally:
        connection.close()
    results = []
    for record_id, record_json, classification, scope_kind, record_project, allowed, score in rows:
        if _accessible((classification, scope_kind, record_project, allowed), project_id):
            results.append({
                "record_id": record_id,
                "score": score,
                "record": json.loads(record_json),
            })
        if len(results) == limit:
            break
    return results


def backup_database(source, destination, repository_root):
    destination = _outside_synchronized_storage(destination, repository_root)
    if destination.exists():
        raise FailureMemoryError("backup target already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_connection = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
    destination_connection = sqlite3.connect(destination)
    try:
        source_connection.backup(destination_connection)
        if destination_connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise FailureMemoryError("backup integrity check failed")
    finally:
        source_connection.close()
        destination_connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        record_set = failure_records.validate_record_set(
            failure_records.load_document(args.input))
        report = build_index(record_set, args.database, args.repository_root)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_bytes(failure_records.canonical_bytes(report))
        print(
            f"failure-memory: {report['status']}; reason={report['reason_code']}; "
            f"real_verified={report['real_verified_records']}/{report['minimum_real_cases']}")
        return 0 if report["status"] == "READY" else 3
    except (failure_records.FailureRecordError, FailureMemoryError, OSError, sqlite3.Error) as exc:
        print(f"failure-memory: ERROR; {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
