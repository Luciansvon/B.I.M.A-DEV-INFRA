"""Deterministic authorization and bounded repository-audit execution."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


REPOSITORY_AUDIT_SCRIPT = Path(__file__).resolve().with_name("repository_audit.py")
REPOSITORY_AUDIT_SPEC = importlib.util.spec_from_file_location(
    "bima_policy_gate_repository_audit", REPOSITORY_AUDIT_SCRIPT)
if REPOSITORY_AUDIT_SPEC is None or REPOSITORY_AUDIT_SPEC.loader is None:
    raise RuntimeError("cannot load the reviewed repository audit adapter")
repository_audit = importlib.util.module_from_spec(REPOSITORY_AUDIT_SPEC)
REPOSITORY_AUDIT_SPEC.loader.exec_module(repository_audit)


MAX_DOCUMENT_BYTES = 65536
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
UTC_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SUPPORTED_OPERATION = "repository-audit"
SUPPORTED_COMMAND = "repository-audit.v1"


class ContractError(ValueError):
    """A contract is malformed or unsupported and cannot be authorized."""


def _exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ContractError(f"{label} fields do not match the v1 contract")


def _identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ContractError(f"{label} is invalid")


def _string(value, label, maximum=256):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ContractError(f"{label} is invalid")


def _integer(value, label, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ContractError(f"{label} is outside its allowed range")


def _unique_strings(value, label, maximum=32):
    if not isinstance(value, list) or len(value) > maximum:
        raise ContractError(f"{label} must be a bounded array")
    for item in value:
        _string(item, label)
    if len(set(value)) != len(value):
        raise ContractError(f"{label} must be unique")


def _relative_path(value, label):
    _string(value, label)
    if "\\" in value or ":" in value:
        raise ContractError(f"{label} must be a relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or any(part in {"", ".git"} for part in path.parts):
        raise ContractError(f"{label} leaves its allowed root")


def _utc(value, label):
    if not isinstance(value, str) or not UTC_TIME.fullmatch(value):
        raise ContractError(f"{label} must be UTC with whole-second precision")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ContractError("duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise ContractError("non-finite JSON number")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ContractError("document is not strict UTF-8 JSON") from exc


def load_document(path):
    if not path.is_file() or path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise ContractError("contract must be a regular file of at most 65536 bytes")
    raw = path.read_bytes()
    return strict_json(raw), raw


def validate_project(value):
    _exact(value, {"schema", "project_id", "repository", "operations"}, "project")
    if value["schema"] != "bima-project.v1":
        raise ContractError("unsupported project schema")
    _identifier(value["project_id"], "project_id")
    _string(value["repository"], "repository")
    operations = value["operations"]
    if not isinstance(operations, list) or not 1 <= len(operations) <= 32:
        raise ContractError("operations must contain 1 to 32 entries")
    ids = []
    for operation in operations:
        _exact(operation, {"id", "command_ref", "required", "timeout_seconds", "output_root", "audit_policy"}, "project operation")
        _identifier(operation["id"], "operation id")
        _string(operation["command_ref"], "command_ref")
        if type(operation["required"]) is not bool:
            raise ContractError("required must be boolean")
        _integer(operation["timeout_seconds"], "timeout_seconds", 1, 3600)
        _relative_path(operation["output_root"], "output_root")
        _relative_path(operation["audit_policy"], "audit_policy")
        ids.append(operation["id"])
    if len(ids) != len(set(ids)):
        raise ContractError("operation ids must be unique")
    return value


def validate_policy(value):
    _exact(value, {"schema", "policy_id", "revision", "projects", "operations", "budget"}, "policy")
    if value["schema"] != "bima-policy.v1":
        raise ContractError("unsupported policy schema")
    _identifier(value["policy_id"], "policy_id")
    _string(value["revision"], "policy revision")
    projects = value["projects"]
    if not isinstance(projects, list) or not 1 <= len(projects) <= 32:
        raise ContractError("policy projects must contain 1 to 32 entries")
    project_ids = []
    for project in projects:
        _exact(project, {"project_id", "repository"}, "policy project")
        _identifier(project["project_id"], "policy project_id")
        _string(project["repository"], "policy repository")
        project_ids.append(project["project_id"])
    if len(project_ids) != len(set(project_ids)):
        raise ContractError("policy project ids must be unique")
    operations = value["operations"]
    if not isinstance(operations, list) or not 1 <= len(operations) <= 32:
        raise ContractError("policy operations must contain 1 to 32 entries")
    ids = []
    for operation in operations:
        _exact(operation, {"id", "command_ref", "max_timeout_seconds", "output_roots", "network_destinations", "credential_names", "max_attempts"}, "policy operation")
        _identifier(operation["id"], "policy operation id")
        _string(operation["command_ref"], "policy command_ref")
        _integer(operation["max_timeout_seconds"], "max_timeout_seconds", 1, 3600)
        _unique_strings(operation["output_roots"], "output_roots")
        if not operation["output_roots"]:
            raise ContractError("output_roots cannot be empty")
        for path in operation["output_roots"]:
            _relative_path(path, "output_roots")
        _unique_strings(operation["network_destinations"], "network_destinations")
        _unique_strings(operation["credential_names"], "credential_names")
        _integer(operation["max_attempts"], "max_attempts", 1, 16)
        ids.append(operation["id"])
    if len(ids) != len(set(ids)):
        raise ContractError("policy operation ids must be unique")
    budget = value["budget"]
    _exact(budget, {"max_calls", "max_runtime_seconds"}, "budget")
    _integer(budget["max_calls"], "max_calls", 1, 100)
    _integer(budget["max_runtime_seconds"], "max_runtime_seconds", 1, 86400)
    return value


def validate_request(value):
    _exact(value, {"schema", "request_id", "project_id", "subject_revision", "operation_id", "command_ref", "output_root", "timeout_seconds", "network_destinations", "credential_names", "attempt", "idempotency_key"}, "request")
    if value["schema"] != "bima-operation-request.v1":
        raise ContractError("unsupported request schema")
    _identifier(value["request_id"], "request_id")
    _identifier(value["project_id"], "project_id")
    if not isinstance(value["subject_revision"], str) or not REVISION.fullmatch(value["subject_revision"]):
        raise ContractError("subject_revision must be a full Git SHA")
    _identifier(value["operation_id"], "operation_id")
    _string(value["command_ref"], "command_ref")
    _relative_path(value["output_root"], "output_root")
    _integer(value["timeout_seconds"], "timeout_seconds", 1, 3600)
    _unique_strings(value["network_destinations"], "network_destinations")
    _unique_strings(value["credential_names"], "credential_names")
    _integer(value["attempt"], "attempt", 1, 16)
    _string(value["idempotency_key"], "idempotency_key", 128)
    return value


def validate_decision(value):
    _exact(value, {"schema", "decision_id", "request_digest", "project_id",
                   "subject_revision", "policy", "rule_ids", "decision",
                   "reason_code", "obligations", "approval_ref", "budget",
                   "actor", "issued_at", "expires_at"}, "decision")
    if value["schema"] != "bima-decision.v1":
        raise ContractError("unsupported decision schema")
    if not isinstance(value["decision_id"], str) or not re.fullmatch(r"dec-[0-9a-f]{32}", value["decision_id"]):
        raise ContractError("decision_id is invalid")
    if not isinstance(value["request_digest"], str) or not SHA256.fullmatch(value["request_digest"]):
        raise ContractError("request_digest is invalid")
    _identifier(value["project_id"], "decision project_id")
    if not isinstance(value["subject_revision"], str) or not REVISION.fullmatch(value["subject_revision"]):
        raise ContractError("decision subject_revision is invalid")
    _exact(value["policy"], {"revision", "sha256"}, "decision policy")
    _string(value["policy"]["revision"], "decision policy revision")
    if not isinstance(value["policy"]["sha256"], str) or not SHA256.fullmatch(value["policy"]["sha256"]):
        raise ContractError("decision policy hash is invalid")
    _unique_strings(value["rule_ids"], "rule_ids")
    if not value["rule_ids"]:
        raise ContractError("rule_ids cannot be empty")
    if value["decision"] not in {"ALLOW", "HUMAN_REQUIRED", "DENY"}:
        raise ContractError("decision value is invalid")
    _string(value["reason_code"], "reason_code")
    obligations = value["obligations"]
    _exact(obligations, {"output_root", "timeout_seconds", "network_destinations",
                         "credential_names"}, "obligations")
    _relative_path(obligations["output_root"], "obligation output_root")
    _integer(obligations["timeout_seconds"], "obligation timeout_seconds", 1, 3600)
    _unique_strings(obligations["network_destinations"], "obligation network_destinations")
    _unique_strings(obligations["credential_names"], "obligation credential_names")
    if value["approval_ref"] is not None:
        _string(value["approval_ref"], "approval_ref")
    _exact(value["budget"], {"max_calls", "max_runtime_seconds", "attempt"}, "decision budget")
    _integer(value["budget"]["max_calls"], "decision max_calls", 1, 100)
    _integer(value["budget"]["max_runtime_seconds"], "decision max_runtime_seconds", 1, 86400)
    _integer(value["budget"]["attempt"], "decision attempt", 1, 16)
    _string(value["actor"], "decision actor")
    issued = _utc(value["issued_at"], "decision issued_at")
    expires = _utc(value["expires_at"], "decision expires_at")
    if expires <= issued:
        raise ContractError("decision expires_at must be after issued_at")
    return value


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _operation(entries, operation_id):
    return next((item for item in entries if item["id"] == operation_id), None)


def evaluate(project, policy, request, expected_policy_sha256, actor, issued_at, expires_at, policy_raw=None):
    validate_project(project)
    validate_policy(policy)
    validate_request(request)
    if not isinstance(expected_policy_sha256, str) or not SHA256.fullmatch(expected_policy_sha256):
        raise ContractError("expected policy hash must be SHA-256")
    _string(actor, "actor")
    issued = _utc(issued_at, "issued_at")
    expires = _utc(expires_at, "expires_at")
    if expires <= issued:
        raise ContractError("expires_at must be after issued_at")
    actual_policy_hash = hashlib.sha256(policy_raw if policy_raw is not None else canonical_bytes(policy)).hexdigest()
    request_hash = digest(request)
    rule_ids = ["PG-DEFAULT-DENY"]
    decision = "DENY"
    reason = "NO_MATCHING_ALLOW_RULE"
    project_operation = _operation(project["operations"], request["operation_id"])
    policy_operation = _operation(policy["operations"], request["operation_id"])

    if actual_policy_hash != expected_policy_sha256:
        reason = "UNTRUSTED_POLICY_HASH"
    elif request["project_id"] != project["project_id"] or not any(
            item["project_id"] == project["project_id"] and
            item["repository"] == project["repository"] for item in policy["projects"]):
        reason = "PROJECT_NOT_ALLOWED"
    elif project_operation is None or policy_operation is None:
        reason = "OPERATION_NOT_ALLOWED"
    elif request["operation_id"] != SUPPORTED_OPERATION or request["command_ref"] != SUPPORTED_COMMAND:
        reason = "UNSUPPORTED_OPERATION"
    elif request["command_ref"] != project_operation["command_ref"] or request["command_ref"] != policy_operation["command_ref"]:
        reason = "COMMAND_MISMATCH"
    elif request["output_root"] != project_operation["output_root"] or request["output_root"] not in policy_operation["output_roots"]:
        reason = "OUTPUT_SCOPE_DENIED"
    elif request["timeout_seconds"] > min(project_operation["timeout_seconds"], policy_operation["max_timeout_seconds"], policy["budget"]["max_runtime_seconds"]):
        reason = "TIMEOUT_BUDGET_EXCEEDED"
    elif request["network_destinations"] != policy_operation["network_destinations"] or request["credential_names"] != policy_operation["credential_names"]:
        reason = "RESOURCE_SCOPE_DENIED"
    elif request["attempt"] > policy_operation["max_attempts"] or request["attempt"] > policy["budget"]["max_calls"]:
        reason = "ATTEMPT_BUDGET_EXCEEDED"
    else:
        decision = "ALLOW"
        reason = "MATCHED_REPOSITORY_AUDIT_RULE"
        rule_ids = ["PG-VERIFY-REPOSITORY-AUDIT-V1"]

    obligations = {
        "output_root": request["output_root"],
        "timeout_seconds": request["timeout_seconds"],
        "network_destinations": request["network_destinations"],
        "credential_names": request["credential_names"],
    }
    decision_seed = {"request_digest": request_hash, "policy_sha256": actual_policy_hash,
                     "actor": actor, "issued_at": issued_at, "expires_at": expires_at}
    return validate_decision({
        "schema": "bima-decision.v1",
        "decision_id": "dec-" + digest(decision_seed)[:32],
        "request_digest": request_hash,
        "project_id": request["project_id"],
        "subject_revision": request["subject_revision"],
        "policy": {"revision": policy["revision"], "sha256": actual_policy_hash},
        "rule_ids": rule_ids,
        "decision": decision,
        "reason_code": reason,
        "obligations": obligations,
        "approval_ref": None,
        "budget": {"max_calls": policy["budget"]["max_calls"],
                   "max_runtime_seconds": policy["budget"]["max_runtime_seconds"],
                   "attempt": request["attempt"]},
        "actor": actor,
        "issued_at": issued_at,
        "expires_at": expires_at,
    })


def _safe_output(root, relative):
    _relative_path(relative, "output_root")
    root = root.resolve()
    candidate = root
    for part in PurePosixPath(relative).parts:
        candidate = candidate / part
        if candidate.exists() and (candidate.is_symlink() or (hasattr(candidate, "is_junction") and candidate.is_junction())):
            raise ContractError("output_root traverses a symlink or junction")
    if not candidate.resolve().is_relative_to(root):
        raise ContractError("output_root leaves repository")
    return candidate


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          timeout=30).stdout.decode("ascii").strip()


def execute_repository_audit(root, project, policy, request, expected_policy_sha256,
                             actor, issued_at, expires_at, policy_raw=None):
    root = root.resolve()
    decision = evaluate(project, policy, request, expected_policy_sha256, actor,
                        issued_at, expires_at, policy_raw)
    now = datetime.now(timezone.utc)
    if decision["decision"] == "ALLOW" and not (
            _utc(issued_at, "issued_at") <= now < _utc(expires_at, "expires_at")):
        decision["decision"] = "DENY"
        decision["reason_code"] = "DECISION_WINDOW_INACTIVE"
    current_revision = _git(root, "rev-parse", "HEAD")
    dirty = bool(_git(root, "status", "--porcelain", "--untracked-files=normal"))
    if decision["decision"] == "ALLOW" and current_revision != request["subject_revision"]:
        decision["decision"] = "DENY"
        decision["reason_code"] = "SUBJECT_REVISION_MISMATCH"
    elif decision["decision"] == "ALLOW" and dirty:
        decision["decision"] = "DENY"
        decision["reason_code"] = "DIRTY_SUBJECT"

    output = _safe_output(root, request["output_root"])
    output.mkdir(parents=True, exist_ok=True)
    (output / "decision.json").write_bytes(canonical_bytes(decision))
    if decision["decision"] != "ALLOW":
        return decision, None

    project_operation = _operation(project["operations"], request["operation_id"])
    audit_output = output / "audit"
    run = subprocess.run(
        [sys.executable, "-I", str(Path(repository_audit.__file__).resolve()),
         "--root", str(root), "--policy", project_operation["audit_policy"],
         "--output", str(audit_output)],
        cwd=root, capture_output=True, text=True, timeout=request["timeout_seconds"])
    result_path = audit_output / "result.json"
    if run.returncode not in {0, 1, 2} or not result_path.is_file():
        raise ContractError("repository audit did not produce its required result")
    result, _ = load_document(result_path)
    if result.get("status") not in {"pass", "fail", "error"}:
        raise ContractError("repository audit result status is invalid")
    if run.returncode != {"pass": 0, "fail": 1, "error": 2}[result["status"]]:
        raise ContractError("repository audit exit code and result disagree")
    return decision, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--trusted-policy", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--expected-policy-sha256", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--issued-at", required=True)
    parser.add_argument("--expires-at", required=True)
    args = parser.parse_args()
    try:
        project, _ = load_document(args.project)
        policy, policy_raw = load_document(args.trusted_policy)
        request, _ = load_document(args.request)
        decision, result = execute_repository_audit(
            args.root, project, policy, request, args.expected_policy_sha256,
            args.actor, args.issued_at, args.expires_at, policy_raw)
        print(f"policy-gate: {decision['decision']}; reason={decision['reason_code']}")
        if decision["decision"] != "ALLOW":
            return 3
        print(f"repository-audit: {result['status']}; findings={len(result['findings'])}")
        return {"pass": 0, "fail": 1, "error": 2}[result["status"]]
    except (ContractError, OSError, subprocess.SubprocessError) as exc:
        print(f"policy-gate: ERROR; {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
