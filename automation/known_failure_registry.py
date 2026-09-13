"""Classify an exact verification failure against a reviewed bounded registry."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


MAX_INPUT_BYTES = 1048576
MAX_ENTRIES = 100
MAX_DIAGNOSTICS = 50
MAX_VALIDITY_DAYS = 90
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
ENTRY_FIELDS = {
    "id", "owner", "reviewed_by", "reason", "issue_ref", "created_at",
    "expires_at", "scope", "outcome_reason_code", "diagnostic_signatures",
}
SCOPE_FIELDS = {
    "project_id", "repository", "check_id", "subject_dirty", "adapter",
    "command_sha256", "policy_sha256", "environment", "equivalence_key",
    "expected_tests",
}


class RegistryError(ValueError):
    """Registry or result input violates the supported contract."""


def _load_result_contract():
    path = Path(__file__).with_name("verification_result_contract.py")
    spec = importlib.util.spec_from_file_location("bima_verification_result_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("verification result contract cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


result_contract = _load_result_contract()


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise RegistryError(f"{label} fields do not match the contract")


def _string(value, label, maximum=512):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise RegistryError(f"{label} is invalid")


def _identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise RegistryError(f"{label} is invalid")


def _sha(value, label):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise RegistryError(f"{label} must be SHA-256")


def _timestamp(value, label):
    if not isinstance(value, str) or not UTC_TIMESTAMP.fullmatch(value):
        raise RegistryError(f"{label} must be a whole-second UTC timestamp")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise RegistryError(f"{label} is not a valid timestamp") from exc


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise RegistryError("duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise RegistryError("non-finite JSON number")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise RegistryError("input is not strict UTF-8 JSON") from exc


def load_json(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise RegistryError("input must be a regular file of at most 1048576 bytes")
    return strict_json(path.read_bytes())


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _validate_identity_hash(value, label, identity_field="id"):
    _exact(value, {identity_field, "sha256"}, label)
    _string(value[identity_field], f"{label} identity", 256)
    _sha(value["sha256"], f"{label} sha256")


def _validate_environment(value, label):
    _exact(value, {"os", "arch", "toolchain"}, label)
    for field in ("os", "arch", "toolchain"):
        _string(value[field], f"{label} {field}", 256)


def _validate_diagnostic(value, label):
    _exact(value, {"tool", "code", "path", "line", "column", "message"}, label)
    for field in ("tool", "code", "path", "message"):
        _string(value[field], f"{label} {field}", 256)
    for field in ("line", "column"):
        if type(value[field]) is not int or value[field] < 1:
            raise RegistryError(f"{label} {field} must be a positive integer")


def _nonnegative_integer(value, label):
    if type(value) is not int or value < 0:
        raise RegistryError(f"{label} must be a non-negative integer")


def validate_result(value):
    try:
        return result_contract.validate_result(value)
    except result_contract.VerificationResultError as exc:
        raise RegistryError(str(exc)) from exc


def _signature_key(value):
    return value["tool"], value["code"], value["path"], value["message_sha256"]


def diagnostic_signatures(result):
    signatures = []
    for diagnostic in result["diagnostics"]:
        signatures.append({
            "tool": diagnostic["tool"],
            "code": diagnostic["code"],
            "path": diagnostic["path"],
            "message_sha256": hashlib.sha256(
                diagnostic["message"].encode("utf-8")).hexdigest(),
        })
    return sorted(signatures, key=_signature_key)


def validate_registry(value):
    _exact(value, {"schema", "entries"}, "registry")
    if value["schema"] != "bima-known-failure-registry.v1":
        raise RegistryError("unsupported registry schema")
    if not isinstance(value["entries"], list) or len(value["entries"]) > MAX_ENTRIES:
        raise RegistryError("registry entries are invalid")
    ids = set()
    match_keys = set()
    for index, entry in enumerate(value["entries"]):
        label = f"registry entry {index}"
        _exact(entry, ENTRY_FIELDS, label)
        _identifier(entry["id"], f"{label} id")
        if entry["id"] in ids:
            raise RegistryError("registry entry ids must be unique")
        ids.add(entry["id"])
        for field in ("owner", "reviewed_by", "reason", "issue_ref"):
            _string(entry[field], f"{label} {field}")
        created = _timestamp(entry["created_at"], f"{label} created_at")
        expires = _timestamp(entry["expires_at"], f"{label} expires_at")
        validity = expires - created
        if validity.total_seconds() <= 0 or validity.total_seconds() > MAX_VALIDITY_DAYS * 86400:
            raise RegistryError("registry entry validity must be positive and at most 90 days")
        _exact(entry["scope"], SCOPE_FIELDS, f"{label} scope")
        for field in ("project_id", "repository", "check_id", "adapter"):
            _string(entry["scope"][field], f"{label} scope {field}")
        if type(entry["scope"]["subject_dirty"]) is not bool:
            raise RegistryError("registry entry subject_dirty must be boolean")
        if entry["scope"]["adapter"] != "rust-libtest-text.v1":
            raise RegistryError("registry entry adapter is unsupported")
        _sha(entry["scope"]["command_sha256"], f"{label} command sha256")
        _sha(entry["scope"]["policy_sha256"], f"{label} policy sha256")
        _validate_environment(entry["scope"]["environment"], f"{label} environment")
        _string(entry["scope"]["equivalence_key"], f"{label} equivalence key", 128)
        if type(entry["scope"]["expected_tests"]) is not int or entry["scope"]["expected_tests"] < 1:
            raise RegistryError("registry entry expected_tests must be positive")
        _string(entry["outcome_reason_code"], f"{label} outcome reason", 128)
        signatures = entry["diagnostic_signatures"]
        if not isinstance(signatures, list) or not 1 <= len(signatures) <= MAX_DIAGNOSTICS:
            raise RegistryError("registry entries require 1 to 50 diagnostic signatures")
        signature_keys = []
        for signature_index, signature in enumerate(signatures):
            _exact(signature, {"tool", "code", "path", "message_sha256"},
                   f"{label} diagnostic signature {signature_index}")
            for field in ("tool", "code", "path"):
                _string(signature[field], f"{label} diagnostic signature {field}", 256)
            if signature["tool"] != "typescript" or not re.fullmatch(r"TS\d+", signature["code"]):
                raise RegistryError("registry diagnostic tool or code is unsupported")
            _sha(signature["message_sha256"], f"{label} diagnostic message sha256")
            signature_keys.append(_signature_key(signature))
        if signature_keys != sorted(set(signature_keys)):
            raise RegistryError("diagnostic signatures must be unique and sorted")
        match_key = (
            entry["scope"]["project_id"], entry["scope"]["repository"],
            entry["scope"]["check_id"], entry["scope"]["subject_dirty"],
            entry["scope"]["adapter"],
            entry["scope"]["command_sha256"], entry["scope"]["policy_sha256"],
            tuple(entry["scope"]["environment"][field]
                  for field in ("os", "arch", "toolchain")),
            entry["scope"]["equivalence_key"], entry["scope"]["expected_tests"],
            entry["outcome_reason_code"], tuple(signature_keys),
        )
        if match_key in match_keys:
            raise RegistryError("registry contains an ambiguous duplicate match")
        match_keys.add(match_key)
    return value


def _entry_matches(entry, result):
    scope = entry["scope"]
    identity = result["identity"]
    return (
        result["verdict"] == "FAIL"
        and scope["project_id"] == identity["project_id"]
        and scope["repository"] == identity["repository"]
        and scope["check_id"] == identity["check_id"]
        and scope["subject_dirty"] == identity["subject_dirty"]
        and scope["adapter"] == result["adapter"]
        and scope["command_sha256"] == result["command"]["sha256"]
        and scope["policy_sha256"] == result["policy"]["sha256"]
        and scope["environment"] == result["environment"]
        and scope["equivalence_key"] == result["attempt"]["equivalence_key"]
        and scope["expected_tests"] == result["outcome"]["expected_tests"]
        and entry["outcome_reason_code"] == result["outcome"]["reason_code"]
        and entry["diagnostic_signatures"] == diagnostic_signatures(result)
    )


def classify(result, registry, as_of):
    validate_result(result)
    validate_registry(registry)
    instant = _timestamp(as_of, "as_of")
    result_hash = hashlib.sha256(canonical_bytes(result)).hexdigest()
    registry_hash = hashlib.sha256(canonical_bytes(registry)).hexdigest()
    classification = "not_applicable" if result["verdict"] != "FAIL" else "unmatched"
    route = "none" if classification == "not_applicable" else "agent"
    match = None
    for entry in registry["entries"]:
        if not _entry_matches(entry, result):
            continue
        created = _timestamp(entry["created_at"], "entry created_at")
        expires = _timestamp(entry["expires_at"], "entry expires_at")
        if instant < created:
            classification, route = "inactive_match", "agent"
        elif instant >= expires:
            classification, route = "expired_match", "agent"
        else:
            classification, route = "known_failure", "machine"
        match = {
            "entry_id": entry["id"],
            "owner": entry["owner"],
            "reviewed_by": entry["reviewed_by"],
            "created_at": entry["created_at"],
            "expires_at": entry["expires_at"],
            "issue_ref": entry["issue_ref"],
        }
        break
    return {
        "schema": "bima-known-failure-classification.v1",
        "classification": classification,
        "route": route,
        "automatic_retry_allowed": False,
        "result": {
            "sha256": result_hash,
            "verdict": result["verdict"],
            "equivalence_key": result["attempt"]["equivalence_key"],
        },
        "registry": {"sha256": registry_hash, "as_of": as_of},
        "match": match,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--as-of", required=True,
                        help="explicit whole-second UTC timestamp, for example 2026-09-10T00:00:00Z")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        classification = classify(load_json(args.result), load_json(args.registry), args.as_of)
        if args.output.is_symlink():
            raise RegistryError("output directory cannot be a symlink")
        args.output.mkdir(parents=True, exist_ok=True)
        if not args.output.is_dir():
            raise RegistryError("output must be a directory")
        destination = args.output / "classification.json"
        if destination.exists() or destination.is_symlink():
            destination.unlink()
        destination.write_bytes(canonical_bytes(classification))
        print(
            "known-failure-registry: "
            f"{classification['classification']}; route={classification['route']}; "
            "automatic_retry_allowed=false"
        )
        return 0
    except (OSError, RegistryError) as exc:
        print(f"known-failure-registry: ERROR; {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
