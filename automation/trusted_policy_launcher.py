"""Launch one reviewed verifier from a pinned, separate DEV-INFRA checkout."""

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


POLICY_GATE_SCRIPT = Path(__file__).resolve().with_name("policy_gate.py")
POLICY_GATE_SPEC = importlib.util.spec_from_file_location(
    "bima_trusted_launcher_policy_gate", POLICY_GATE_SCRIPT)
if POLICY_GATE_SPEC is None or POLICY_GATE_SPEC.loader is None:
    raise RuntimeError("cannot load the reviewed policy gate")
policy_gate = importlib.util.module_from_spec(POLICY_GATE_SPEC)
POLICY_GATE_SPEC.loader.exec_module(policy_gate)


IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_ENV = {
    "BIMA_TRUSTED_ACTOR",
    "BIMA_SUBJECT_REPOSITORY",
    "BIMA_WORKFLOW_REPOSITORY",
    "BIMA_WORKFLOW_REF",
    "BIMA_WORKFLOW_SHA",
    "BIMA_RUN_ID",
    "BIMA_RUN_ATTEMPT",
}
BUNDLE_FIELDS = {
    "schema", "bundle_id", "workflow_repository", "workflow_path",
    "policy_path", "policy_sha256", "operation_id", "decision_ttl_seconds",
}


class LauncherError(ValueError):
    """The trusted launch boundary could not be established."""

    def __init__(self, reason_code, message):
        super().__init__(message)
        self.reason_code = reason_code


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise LauncherError("INVALID_TRUST_BUNDLE", f"{label} fields do not match the contract")


def _relative_path(value, label):
    if not isinstance(value, str) or not value or len(value) > 256 or "\\" in value or ":" in value:
        raise LauncherError("INVALID_TRUST_PATH", f"{label} must be a bounded relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or any(part in {"", ".git"} for part in path.parts):
        raise LauncherError("INVALID_TRUST_PATH", f"{label} leaves its allowed root")
    return path


def _safe_file(root, relative, label):
    relative = _relative_path(relative, label)
    root = root.resolve()
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.exists() and (
                candidate.is_symlink()
                or (hasattr(candidate, "is_junction") and candidate.is_junction())):
            raise LauncherError("UNSAFE_TRUST_PATH", f"{label} traverses a link or junction")
    if not candidate.resolve().is_relative_to(root):
        raise LauncherError("INVALID_TRUST_PATH", f"{label} leaves its allowed root")
    if not candidate.is_file():
        raise LauncherError("TRUST_FILE_MISSING", f"{label} is not a regular file")
    return candidate


def _safe_output(path, infra_root, subject_root):
    path = path.resolve()
    for root in (infra_root.resolve(), subject_root.resolve()):
        if path == root or path.is_relative_to(root):
            raise LauncherError("UNSAFE_EVIDENCE_OUTPUT", "launcher evidence must stay outside both checkouts")
    candidate = path.parent
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    if candidate.is_symlink() or (hasattr(candidate, "is_junction") and candidate.is_junction()):
        raise LauncherError("UNSAFE_EVIDENCE_OUTPUT", "launcher evidence parent is a link or junction")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _git(root, *args):
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True,
            timeout=30).stdout.decode("utf-8").strip()
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        raise LauncherError("GIT_IDENTITY_ERROR", "cannot establish checkout identity") from exc


def validate_bundle(value, bundle_id):
    _exact(value, BUNDLE_FIELDS, "trust bundle")
    if value["schema"] != "bima-trust-bundle.v1":
        raise LauncherError("INVALID_TRUST_BUNDLE", "unsupported trust bundle schema")
    if not isinstance(value["bundle_id"], str) or not IDENTIFIER.fullmatch(value["bundle_id"]):
        raise LauncherError("INVALID_TRUST_BUNDLE", "bundle_id is invalid")
    if value["bundle_id"] != bundle_id:
        raise LauncherError("INVALID_TRUST_BUNDLE", "bundle identity does not match its requested ID")
    if not isinstance(value["workflow_repository"], str) or not value["workflow_repository"]:
        raise LauncherError("INVALID_TRUST_BUNDLE", "workflow repository is invalid")
    workflow_path = _relative_path(value["workflow_path"], "workflow_path")
    if not str(workflow_path).startswith(".github/workflows/") or workflow_path.suffix != ".yml":
        raise LauncherError("INVALID_TRUST_BUNDLE", "workflow_path is not a reusable workflow")
    _relative_path(value["policy_path"], "policy_path")
    if not isinstance(value["policy_sha256"], str) or not SHA256.fullmatch(value["policy_sha256"]):
        raise LauncherError("INVALID_TRUST_BUNDLE", "policy_sha256 is invalid")
    if not isinstance(value["operation_id"], str) or not IDENTIFIER.fullmatch(value["operation_id"]):
        raise LauncherError("INVALID_TRUST_BUNDLE", "operation_id is invalid")
    if type(value["decision_ttl_seconds"]) is not int or not 30 <= value["decision_ttl_seconds"] <= 600:
        raise LauncherError("INVALID_TRUST_BUNDLE", "decision TTL is outside 30 to 600 seconds")
    return value


def _required_environment(environment):
    missing = sorted(name for name in REQUIRED_ENV if not environment.get(name))
    if missing:
        raise LauncherError("TRUSTED_ENV_MISSING", "trusted launcher environment is incomplete")
    if not REVISION.fullmatch(environment["BIMA_WORKFLOW_SHA"]):
        raise LauncherError("WORKFLOW_SHA_INVALID", "workflow SHA must be a full lowercase Git revision")
    try:
        attempt = int(environment["BIMA_RUN_ATTEMPT"])
    except ValueError as exc:
        raise LauncherError("RUN_ATTEMPT_INVALID", "run attempt is not an integer") from exc
    if not 1 <= attempt <= 16:
        raise LauncherError("RUN_ATTEMPT_INVALID", "run attempt is outside 1 to 16")
    return attempt


def _decision(decision, reason_code, environment, bundle_id=None,
              policy_sha256=None, policy_gate_decision=None, verifier_launched=False):
    return {
        "schema": "bima-trusted-launcher-decision.v1",
        "decision": decision,
        "reason_code": reason_code,
        "workflow_repository": environment.get("BIMA_WORKFLOW_REPOSITORY"),
        "workflow_sha": environment.get("BIMA_WORKFLOW_SHA"),
        "subject_repository": environment.get("BIMA_SUBJECT_REPOSITORY"),
        "bundle_id": bundle_id,
        "policy_sha256": policy_sha256,
        "policy_gate_decision": policy_gate_decision,
        "verifier_launched": verifier_launched,
    }


def launch(infra_root, subject_root, bundle_id, project_path, environment, now=None):
    attempt = _required_environment(environment)
    if not IDENTIFIER.fullmatch(bundle_id):
        raise LauncherError("INVALID_BUNDLE_ID", "bundle ID is invalid")
    infra_root = infra_root.resolve()
    subject_root = subject_root.resolve()
    if (infra_root == subject_root or infra_root.is_relative_to(subject_root)
            or subject_root.is_relative_to(infra_root)):
        raise LauncherError("CHECKOUTS_NOT_SEPARATE", "infrastructure and subject checkouts overlap")
    launcher_path = Path(__file__).resolve()
    if not launcher_path.is_relative_to(infra_root):
        raise LauncherError("UNTRUSTED_LAUNCHER_PATH", "launcher is not executing from the infrastructure checkout")

    workflow_sha = environment["BIMA_WORKFLOW_SHA"]
    if _git(infra_root, "rev-parse", "HEAD") != workflow_sha:
        raise LauncherError("INFRA_REVISION_MISMATCH", "infrastructure checkout does not match workflow SHA")
    if _git(infra_root, "status", "--porcelain", "--untracked-files=normal"):
        raise LauncherError("DIRTY_INFRA_CHECKOUT", "infrastructure checkout is dirty")

    bundle_relative = f"policies/trust-bundles/{bundle_id}.json"
    bundle_file = _safe_file(infra_root, bundle_relative, "trust bundle")
    try:
        bundle = validate_bundle(policy_gate.strict_json(bundle_file.read_bytes()), bundle_id)
    except policy_gate.ContractError as exc:
        raise LauncherError("INVALID_TRUST_BUNDLE", "trust bundle is not strict JSON") from exc

    if environment["BIMA_WORKFLOW_REPOSITORY"] != bundle["workflow_repository"]:
        raise LauncherError("WORKFLOW_REPOSITORY_MISMATCH", "job workflow repository is not trusted")
    expected_workflow_ref = (
        f"{bundle['workflow_repository']}/{bundle['workflow_path']}@{workflow_sha}")
    if environment["BIMA_WORKFLOW_REF"] != expected_workflow_ref:
        raise LauncherError("WORKFLOW_REF_MISMATCH", "job workflow ref is not bound to the trusted SHA")

    policy_file = _safe_file(infra_root, bundle["policy_path"], "trusted policy")
    policy_raw = policy_file.read_bytes()
    actual_policy_sha256 = hashlib.sha256(policy_raw).hexdigest()
    if actual_policy_sha256 != bundle["policy_sha256"]:
        raise LauncherError("TRUSTED_POLICY_HASH_MISMATCH", "trusted policy bytes do not match the bundle")
    try:
        policy = policy_gate.validate_policy(policy_gate.strict_json(policy_raw))
    except policy_gate.ContractError as exc:
        raise LauncherError("INVALID_TRUSTED_POLICY", "trusted policy violates its contract") from exc

    project_file = _safe_file(subject_root, project_path, "project declaration")
    try:
        project = policy_gate.validate_project(policy_gate.strict_json(project_file.read_bytes()))
    except policy_gate.ContractError as exc:
        raise LauncherError("INVALID_PROJECT_DECLARATION", "project declaration violates its contract") from exc
    if project["repository"] != environment["BIMA_SUBJECT_REPOSITORY"]:
        raise LauncherError("SUBJECT_REPOSITORY_MISMATCH", "project declaration does not match caller repository")
    project_operation = next(
        (item for item in project["operations"] if item["id"] == bundle["operation_id"]), None)
    if project_operation is None:
        raise LauncherError("PROJECT_OPERATION_MISSING", "project does not declare the trusted operation")

    subject_revision = _git(subject_root, "rev-parse", "HEAD")
    run_seed = {
        "repository": environment["BIMA_SUBJECT_REPOSITORY"],
        "subject_revision": subject_revision,
        "run_id": environment["BIMA_RUN_ID"],
        "attempt": attempt,
        "operation_id": bundle["operation_id"],
    }
    run_digest = hashlib.sha256(policy_gate.canonical_bytes(run_seed)).hexdigest()
    request = {
        "schema": "bima-operation-request.v1",
        "request_id": f"run-{run_digest[:24]}",
        "project_id": project["project_id"],
        "subject_revision": subject_revision,
        "operation_id": bundle["operation_id"],
        "command_ref": project_operation["command_ref"],
        "output_root": project_operation["output_root"],
        "timeout_seconds": project_operation["timeout_seconds"],
        "network_destinations": [],
        "credential_names": [],
        "attempt": attempt,
        "idempotency_key": run_digest,
    }
    now = now or datetime.now(timezone.utc)
    now = now.astimezone(timezone.utc).replace(microsecond=0)
    expires = now + timedelta(seconds=bundle["decision_ttl_seconds"])
    issued_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    expires_at = expires.strftime("%Y-%m-%dT%H:%M:%SZ")
    actor = f"github-actions:{environment['BIMA_TRUSTED_ACTOR']}"
    decision, result = policy_gate.execute_repository_audit(
        subject_root, project, policy, request, bundle["policy_sha256"], actor,
        issued_at, expires_at, policy_raw)
    launched = decision["decision"] == "ALLOW" and result is not None
    return _decision(
        decision["decision"], decision["reason_code"], environment, bundle_id,
        bundle["policy_sha256"], decision["decision"], launched), result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--infra-root", type=Path, required=True)
    parser.add_argument("--subject-root", type=Path, required=True)
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("--project-path", default=".bima/project.json")
    parser.add_argument("--evidence-output", type=Path, required=True)
    args = parser.parse_args()
    environment = {name: os.environ.get(name, "") for name in REQUIRED_ENV}
    output = None
    try:
        output = _safe_output(args.evidence_output, args.infra_root, args.subject_root)
        decision, result = launch(
            args.infra_root, args.subject_root, args.bundle_id, args.project_path,
            environment)
        output.write_bytes(policy_gate.canonical_bytes(decision))
        print(
            f"trusted-launcher: {decision['decision']}; "
            f"reason={decision['reason_code']}; verifier_launched={str(decision['verifier_launched']).lower()}")
        if decision["decision"] != "ALLOW":
            return 3
        return {"pass": 0, "fail": 1, "error": 2}[result["status"]]
    except LauncherError as exc:
        decision = _decision("DENY", exc.reason_code, environment, args.bundle_id)
        if output is not None:
            output.write_bytes(policy_gate.canonical_bytes(decision))
        print(f"trusted-launcher: DENY; reason={exc.reason_code}; verifier_launched=false", file=sys.stderr)
        return 3
    except (OSError, policy_gate.ContractError, subprocess.SubprocessError) as exc:
        decision = _decision("ERROR", "LAUNCHER_ERROR", environment, args.bundle_id)
        if output is not None:
            output.write_bytes(policy_gate.canonical_bytes(decision))
        print(f"trusted-launcher: ERROR; {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
