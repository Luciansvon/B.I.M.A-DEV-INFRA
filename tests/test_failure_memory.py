import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation/failure_memory.py"
RECORDS_SCRIPT = ROOT / "automation/failure_records.py"
FIXTURE = ROOT / "tests/fixtures/failure-records/records.json"
PRODUCTION_RECORDS = ROOT / "failure-records/records.json"

MEMORY_SPEC = importlib.util.spec_from_file_location("failure_memory", SCRIPT)
memory_module = importlib.util.module_from_spec(MEMORY_SPEC)
MEMORY_SPEC.loader.exec_module(memory_module)
RECORDS_SPEC = importlib.util.spec_from_file_location("failure_records_test", RECORDS_SCRIPT)
records_module = importlib.util.module_from_spec(RECORDS_SPEC)
RECORDS_SPEC.loader.exec_module(records_module)


class FailureMemoryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = records_module.load_document(FIXTURE)

    def ready_corpus(self, count=100):
        template = self.fixture["records"][0]
        records = []
        for index in range(count):
            record = copy.deepcopy(template)
            record["id"] = f"case-{index:03d}"
            record["case_kind"] = "real"
            record["failure"]["signature_sha256"] = f"{index + 1:064x}"
            records.append(record)
        return {
            "schema": "bima-failure-record-set.v1",
            "dataset_id": "ready-test-corpus",
            "records": records,
        }

    def test_production_corpus_is_blocked_and_creates_no_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            database = temporary / "memory.sqlite3"
            report = temporary / "report.json"
            run = subprocess.run(
                [
                    sys.executable, "-I", str(SCRIPT),
                    "--input", str(PRODUCTION_RECORDS),
                    "--database", str(database),
                    "--repository-root", str(ROOT),
                    "--report", str(report),
                ],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(run.returncode, 3, run.stderr)
            decision = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(decision["status"], "BLOCKED")
            self.assertEqual(decision["reason_code"], "INSUFFICIENT_REAL_CASES")
            self.assertEqual(decision["real_verified_records"], 0)
            self.assertFalse(database.exists())

    def test_ready_corpus_builds_searchable_index_and_round_trips(self):
        corpus = self.ready_corpus()
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "memory.sqlite3"
            report = memory_module.build_index(corpus, database, ROOT)
            self.assertEqual(report["status"], "READY")
            self.assertEqual(report["indexed_active_records"], 100)
            self.assertTrue(database.is_file())
            exported = memory_module.export_record_set(database)
            self.assertEqual(
                records_module.canonical_bytes(exported),
                records_module.canonical_bytes(corpus),
            )
            matches = memory_module.search(
                database, "synthetic confirmed cause", "fixture-project", limit=5)
            self.assertEqual(len(matches), 5)
            self.assertEqual(
                memory_module.search(database, "confirmed cause", "other-project"), [])

    def test_invalidated_records_are_retained_but_not_indexed(self):
        corpus = self.ready_corpus(101)
        corpus["records"][0]["status"] = "INVALIDATED"
        corpus["records"][0]["invalidation_reason"] = "No longer valid."
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "memory.sqlite3"
            report = memory_module.build_index(corpus, database, ROOT)
            self.assertEqual(report["real_verified_records"], 100)
            self.assertEqual(report["indexed_active_records"], 100)
            exported = memory_module.export_record_set(database)
            self.assertEqual(exported["records"][0]["status"], "INVALIDATED")

    def test_inactive_real_records_cannot_satisfy_the_corpus_gate(self):
        corpus = self.ready_corpus()
        corpus["records"][0]["status"] = "INVALIDATED"
        corpus["records"][0]["invalidation_reason"] = "No longer valid."
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "memory.sqlite3"
            report = memory_module.build_index(corpus, database, ROOT)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(report["real_verified_records"], 99)
            self.assertFalse(database.exists())

    def test_restricted_records_require_explicit_project_access(self):
        corpus = self.ready_corpus()
        for record in corpus["records"]:
            record["access"] = {
                "classification": "restricted",
                "allowed_projects": ["allowed-project"],
            }
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "memory.sqlite3"
            memory_module.build_index(corpus, database, ROOT)
            self.assertEqual(
                memory_module.search(database, "confirmed cause", "fixture-project"), [])
            self.assertTrue(
                memory_module.search(database, "confirmed cause", "allowed-project"))

    def test_database_rejects_repository_sync_and_network_locations(self):
        corpus = self.ready_corpus()
        with self.assertRaises(memory_module.FailureMemoryError):
            memory_module.build_index(corpus, ROOT / ".artifacts/memory.sqlite3", ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(memory_module.FailureMemoryError):
                memory_module.build_index(
                    corpus, Path(temporary) / "OneDrive/memory.sqlite3", ROOT)
        with self.assertRaises(memory_module.FailureMemoryError):
            memory_module.build_index(
                corpus, Path("//server/share/memory.sqlite3"), ROOT)

    def test_backup_is_integrity_checked_and_rebuildable(self):
        corpus = self.ready_corpus()
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            database = temporary / "memory.sqlite3"
            backup = temporary / "backup.sqlite3"
            rebuilt = temporary / "rebuilt.sqlite3"
            memory_module.build_index(corpus, database, ROOT)
            memory_module.backup_database(database, backup, ROOT)
            self.assertEqual(
                records_module.canonical_bytes(memory_module.export_record_set(backup)),
                records_module.canonical_bytes(corpus),
            )
            exported = memory_module.export_record_set(database)
            memory_module.build_index(exported, rebuilt, ROOT)
            self.assertEqual(
                records_module.canonical_bytes(memory_module.export_record_set(rebuilt)),
                records_module.canonical_bytes(corpus),
            )


if __name__ == "__main__":
    unittest.main()
