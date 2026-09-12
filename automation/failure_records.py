"""Validate and canonicalize portable reviewed failure records."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys


MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_RECORDS = 10000
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
RECORD_FIELDS = {
    "schema", "id", "case_kind", "status", "scope", "failure", "cause",
    "fix", "review", "access", "supersedes", "superseded_by",
    "invalidation_reason", "expires_at",
}


class FailureRecordError(ValueError):
    """A failure record set is malformed or violates promotion policy."""


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise FailureRecordError(f"{label} fields do not match the v1 contract")


def _string(value, label, maximum=512):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise FailureRecordError(f"{label} is invalid")


def _identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise FailureRecordError(f"{label} is invalid")


def _timestamp(value, label):
    if not isinstance(value, str) or not UTC_TIMESTAMP.fullmatch(value):
        raise FailureRecordError(f"{label} must be a whole-second UTC timestamp")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise FailureRecordError(f"{label} is not a valid timestamp") from exc


def _nullable_timestamp(value, label):
    return None if value is None else _timestamp(value, label)


def _bounded_unique_strings(value, label, minimum=0, maximum=32):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise FailureRecordError(f"{label} is outside its item bounds")
    for item in value:
        _string(item, label)
    if value != sorted(set(value)):
        raise FailureRecordError(f"{label} must be unique and sorted")


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise FailureRecordError("duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise FailureRecordError("non-finite JSON number")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        multiline = "input is not strict UTF-8 JSON"
        raise FailureRecordError(multiline) from exc


def load_document(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise FailureRecordError("input must be a regular file within the byte limit")
    return strict_json(path.read_bytes())


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _environment(value, label):
    _exact(value, {"os", "arch", "toolchain"}, label)
    for field in ("os", "arch", "toolchain"):
        _string(value[field], f"{label} {field}", 256)


def _validate_scope(value, label):
    _exact(value, {
        "kind", "promotion_basis", "project_id", "repositories", "command_ref",
        "rule_version", "environment",
    }, label)
    if value["kind"] not in {"project", "global"}:
        raise FailureRecordError(f"{label} kind is invalid")
    if value["promotion_basis"] not in {
            "project", "shared_infrastructure", "repeated_root_cause"}:
        raise FailureRecordError(f"{label} promotion basis is invalid")
    _bounded_unique_strings(value["repositories"], f"{label} repositories", 1)
    _string(value["command_ref"], f"{label} command_ref", 256)
    _string(value["rule_version"], f"{label} rule_version", 128)
    _environment(value["environment"], f"{label} environment")
    if value["kind"] == "project":
        _identifier(value["project_id"], f"{label} project_id")
        if value["promotion_basis"] != "project" or len(value["repositories"]) != 1:
            raise FailureRecordError("project scope must remain project-owned")
    else:
        if value["project_id"] is not None or value["promotion_basis"] == "project":
            raise FailureRecordError("global scope cannot use project ownership")
        if (value["promotion_basis"] == "repeated_root_cause"
                and len(value["repositories"]) < 2):
            raise FailureRecordError("repeated global cause requires at least two repositories")


def validate_record(value):
    _exact(value, RECORD_FIELDS, "record")
    if value["schema"] != "bima-failure-record.v1":
        raise FailureRecordError("unsupported failure record schema")
    _identifier(value["id"], "record id")
    if value["case_kind"] not in {"real", "synthetic"}:
        raise FailureRecordError("record case_kind is invalid")
    if value["status"] not in {
            "ACTIVE", "SUPERSEDED", "EXPIRED", "INVALIDATED",
            "REVALIDATION_REQUIRED"}:
        raise FailureRecordError("record status is invalid")
    _validate_scope(value["scope"], "record scope")

    _exact(value["failure"], {
        "observed_at", "reason_code", "signature_sha256", "reproduction_refs",
    }, "record failure")
    _timestamp(value["failure"]["observed_at"], "failure observed_at")
    _string(value["failure"]["reason_code"], "failure reason_code", 128)
    if not isinstance(value["failure"]["signature_sha256"], str) or not SHA256.fullmatch(
            value["failure"]["signature_sha256"]):
        raise FailureRecordError("failure signature must be SHA-256")
    _bounded_unique_strings(value["failure"]["reproduction_refs"], "reproduction refs", 1)

    _exact(value["cause"], {"summary", "confirmed_at", "evidence_refs"}, "record cause")
    _string(value["cause"]["summary"], "cause summary", 1024)
    _timestamp(value["cause"]["confirmed_at"], "cause confirmed_at")
    _bounded_unique_strings(value["cause"]["evidence_refs"], "cause evidence refs", 1)

    _exact(value["fix"], {"summary", "revision", "verification_refs"}, "record fix")
    _string(value["fix"]["summary"], "fix summary", 1024)
    if not isinstance(value["fix"]["revision"], str) or not REVISION.fullmatch(value["fix"]["revision"]):
        raise FailureRecordError("fix revision must be a full Git SHA")
    _bounded_unique_strings(value["fix"]["verification_refs"], "fix verification refs", 1)

    _exact(value["review"], {
        "owner", "reviewed_by", "reviewed_at", "last_revalidated_at",
    }, "record review")
    _string(value["review"]["owner"], "review owner", 256)
    _string(value["review"]["reviewed_by"], "reviewed_by", 256)
    if value["review"]["owner"] == value["review"]["reviewed_by"]:
        raise FailureRecordError("reviewer must be independent from the record owner")
    reviewed_at = _timestamp(value["review"]["reviewed_at"], "reviewed_at")
    revalidated_at = _timestamp(
        value["review"]["last_revalidated_at"], "last_revalidated_at")
    if revalidated_at < reviewed_at:
        raise FailureRecordError("last revalidation cannot precede review")

    _exact(value["access"], {"classification", "allowed_projects"}, "record access")
    if value["access"]["classification"] not in {"public", "internal", "restricted"}:
        raise FailureRecordError("access classification is invalid")
    _bounded_unique_strings(value["access"]["allowed_projects"], "allowed projects")
    if (value["access"]["classification"] == "restricted"
            and not value["access"]["allowed_projects"]):
        raise FailureRecordError("restricted records require an access allowlist")

    _bounded_unique_strings(value["supersedes"], "supersedes")
    if value["id"] in value["supersedes"]:
        raise FailureRecordError("a record cannot supersede itself")
    if value["superseded_by"] is not None:
        _identifier(value["superseded_by"], "superseded_by")
    if value["invalidation_reason"] is not None:
        _string(value["invalidation_reason"], "invalidation_reason")
    expires_at = _nullable_timestamp(value["expires_at"], "expires_at")

    if value["status"] == "ACTIVE" and (
            value["superseded_by"] is not None or value["invalidation_reason"] is not None):
        raise FailureRecordError("active records cannot be superseded or invalidated")
    if value["status"] == "SUPERSEDED" and value["superseded_by"] is None:
        raise FailureRecordError("superseded records require superseded_by")
    if value["status"] in {"INVALIDATED", "REVALIDATION_REQUIRED"} and not value["invalidation_reason"]:
        raise FailureRecordError("invalidated records require a reason")
    if value["status"] == "EXPIRED" and expires_at is None:
        raise FailureRecordError("expired records require expires_at")
    return value


def validate_record_set(value):
    _exact(value, {"schema", "dataset_id", "records"}, "record set")
    if value["schema"] != "bima-failure-record-set.v1":
        raise FailureRecordError("unsupported record set schema")
    _identifier(value["dataset_id"], "dataset_id")
    if not isinstance(value["records"], list) or len(value["records"]) > MAX_RECORDS:
        raise FailureRecordError("record set is outside its item bounds")
    ids = []
    for record in value["records"]:
        validate_record(record)
        ids.append(record["id"])
    if ids != sorted(set(ids)):
        raise FailureRecordError("record IDs must be unique and sorted")
    known = set(ids)
    records_by_id = {record["id"]: record for record in value["records"]}
    for record in value["records"]:
        for prior in record["supersedes"]:
            if prior not in known:
                raise FailureRecordError("supersedes references an unknown record")
            prior_record = records_by_id[prior]
            if (prior_record["status"] != "SUPERSEDED"
                    or prior_record["superseded_by"] != record["id"]):
                raise FailureRecordError("supersession links must be reciprocal")
        if record["superseded_by"] is not None and record["superseded_by"] not in known:
            raise FailureRecordError("superseded_by references an unknown record")
        if (record["superseded_by"] is not None
                and record["id"] not in records_by_id[record["superseded_by"]]["supersedes"]):
            raise FailureRecordError("supersession links must be reciprocal")
    return value


def summarize(value):
    validate_record_set(value)
    canonical = canonical_bytes(value)
    records = value["records"]
    return {
        "schema": "bima-failure-record-summary.v1",
        "dataset_id": value["dataset_id"],
        "record_set_sha256": hashlib.sha256(canonical).hexdigest(),
        "total_records": len(records),
        "real_verified_records": sum(
            record["case_kind"] == "real" and record["status"] == "ACTIVE"
            for record in records),
        "synthetic_records": sum(record["case_kind"] == "synthetic" for record in records),
        "active_records": sum(record["status"] == "ACTIVE" for record in records),
        "projects": sorted({
            project
            for record in records
            for project in ([record["scope"]["project_id"]]
                            if record["scope"]["project_id"] else [])
        }),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        records = validate_record_set(load_document(args.input))
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "records.json").write_bytes(canonical_bytes(records))
        summary = summarize(records)
        (args.output / "summary.json").write_bytes(canonical_bytes(summary))
        print(
            f"failure-records: pass; total={summary['total_records']}; "
            f"real_verified={summary['real_verified_records']}")
        return 0
    except (FailureRecordError, OSError) as exc:
        print(f"failure-records: error; {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
