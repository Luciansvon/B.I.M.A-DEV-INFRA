"""Evaluate evidence and demand gates for optional DEV-INFRA experiments."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


MAX_INPUT_BYTES = 1024 * 1024
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CAPABILITIES = {
    "graphify-context", "release-proof", "local-qa-slm", "sandbox",
    "database-verifier", "durable-workflow", "security-response",
    "fleet-telemetry",
}


class ExperimentGateError(ValueError):
    """Experiment request is malformed and cannot be evaluated."""


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ExperimentGateError(f"{label} fields do not match the v1 contract")


def _string(value, label, maximum=512):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ExperimentGateError(f"{label} is invalid")


def _identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ExperimentGateError(f"{label} is invalid")


def _nonnegative(value, label, maximum=10**12):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ExperimentGateError(f"{label} is outside its allowed range")


def _sorted_strings(value, label, minimum=0, maximum=32):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ExperimentGateError(f"{label} is outside its item bounds")
    for item in value:
        _string(item, label)
    if value != sorted(set(value)):
        raise ExperimentGateError(f"{label} must be unique and sorted")


def _relative_path(value, label):
    _string(value, label, 256)
    if "\\" in value or ":" in value:
        raise ExperimentGateError(f"{label} must be a relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or ".git" in path.parts:
        raise ExperimentGateError(f"{label} leaves its allowed root")


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ExperimentGateError("duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise ExperimentGateError("non-finite JSON number")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ExperimentGateError("input is not strict UTF-8 JSON") from exc


def load_document(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ExperimentGateError("input must be a regular file within the byte limit")
    return strict_json(path.read_bytes())


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def validate_request(value):
    _exact(value, {
        "schema", "experiment_id", "capability", "baseline", "dataset",
        "acceptance_thresholds", "budget", "permissions", "reject_criteria",
        "rollback", "demand_evidence",
    }, "experiment request")
    if value["schema"] != "bima-experiment-request.v1":
        raise ExperimentGateError("unsupported experiment request schema")
    _identifier(value["experiment_id"], "experiment_id")
    if value["capability"] not in CAPABILITIES:
        raise ExperimentGateError("capability is unsupported")

    _exact(value["baseline"], {"id", "evidence_refs"}, "baseline")
    _identifier(value["baseline"]["id"], "baseline id")
    _sorted_strings(value["baseline"]["evidence_refs"], "baseline evidence refs", 1)

    _exact(value["dataset"], {"id", "sha256", "verified_cases", "held_out"}, "dataset")
    _identifier(value["dataset"]["id"], "dataset id")
    if not isinstance(value["dataset"]["sha256"], str) or not SHA256.fullmatch(value["dataset"]["sha256"]):
        raise ExperimentGateError("dataset sha256 is invalid")
    _nonnegative(value["dataset"]["verified_cases"], "verified_cases", 10**7)
    if type(value["dataset"]["held_out"]) is not bool:
        raise ExperimentGateError("held_out must be boolean")

    thresholds = value["acceptance_thresholds"]
    if not isinstance(thresholds, list) or not 1 <= len(thresholds) <= 32:
        raise ExperimentGateError("acceptance thresholds are outside their item bounds")
    metric_names = []
    for threshold in thresholds:
        _exact(threshold, {"metric", "operator", "value", "unit"}, "acceptance threshold")
        _identifier(threshold["metric"], "acceptance metric")
        if threshold["operator"] not in {"lt", "lte", "eq", "gte", "gt"}:
            raise ExperimentGateError("acceptance operator is invalid")
        if type(threshold["value"]) is not int:
            raise ExperimentGateError("acceptance value must be an integer")
        _string(threshold["unit"], "acceptance unit", 64)
        metric_names.append(threshold["metric"])
    if metric_names != sorted(set(metric_names)):
        raise ExperimentGateError("acceptance metrics must be unique and sorted")

    _exact(value["budget"], {
        "max_runtime_seconds", "max_storage_bytes", "max_network_calls",
        "max_agent_calls",
    }, "budget")
    _nonnegative(value["budget"]["max_runtime_seconds"], "max_runtime_seconds", 86400)
    if value["budget"]["max_runtime_seconds"] < 1:
        raise ExperimentGateError("runtime budget must be positive")
    _nonnegative(value["budget"]["max_storage_bytes"], "max_storage_bytes")
    _nonnegative(value["budget"]["max_network_calls"], "max_network_calls", 10000)
    _nonnegative(value["budget"]["max_agent_calls"], "max_agent_calls", 100)

    _exact(value["permissions"], {
        "write_roots", "network_destinations", "credential_names",
    }, "permissions")
    for field in ("write_roots", "network_destinations", "credential_names"):
        _sorted_strings(value["permissions"][field], f"permission {field}")
    for path in value["permissions"]["write_roots"]:
        _relative_path(path, "write root")

    _sorted_strings(value["reject_criteria"], "reject criteria", 1)
    _exact(value["rollback"], {"owner", "steps"}, "rollback")
    _string(value["rollback"]["owner"], "rollback owner", 256)
    _sorted_strings(value["rollback"]["steps"], "rollback steps", 1)

    demands = value["demand_evidence"]
    if not isinstance(demands, list) or len(demands) > 32:
        raise ExperimentGateError("demand evidence is outside its item bounds")
    keys = []
    project_ids = []
    repositories = []
    for demand in demands:
        _exact(demand, {
            "project_id", "repository", "requirement_ref", "reviewed_by",
        }, "demand evidence")
        _identifier(demand["project_id"], "demand project_id")
        for field in ("repository", "requirement_ref", "reviewed_by"):
            _string(demand[field], f"demand {field}")
        keys.append((demand["project_id"], demand["repository"]))
        project_ids.append(demand["project_id"])
        repositories.append(demand["repository"])
    if keys != sorted(set(keys)):
        raise ExperimentGateError("demand evidence must be unique and sorted")
    if len(project_ids) != len(set(project_ids)) or len(repositories) != len(set(repositories)):
        raise ExperimentGateError("each demand must identify a distinct project and repository")
    return value


def evaluate(value):
    validate_request(value)
    request_sha256 = hashlib.sha256(canonical_bytes(value)).hexdigest()
    projects = {item["repository"] for item in value["demand_evidence"]}
    status = "READY"
    reason = "DEMAND_AND_EVIDENCE_GATES_SATISFIED"
    if len(projects) < 2:
        status = "BLOCKED"
        reason = "INSUFFICIENT_CROSS_PROJECT_DEMAND"
    elif value["capability"] == "local-qa-slm" and (
            value["dataset"]["verified_cases"] < 1000
            or not value["dataset"]["held_out"]):
        status = "BLOCKED"
        reason = "MODEL_BENCHMARK_GATE_UNMET"
    return {
        "schema": "bima-experiment-decision.v1",
        "experiment_id": value["experiment_id"],
        "capability": value["capability"],
        "request_sha256": request_sha256,
        "status": status,
        "reason_code": reason,
        "distinct_projects": len(projects),
        "requires_policy_authorization": True,
        "execution_started": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        decision = evaluate(load_document(args.request))
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "decision.json").write_bytes(canonical_bytes(decision))
        print(
            f"experiment-gate: {decision['status']}; reason={decision['reason_code']}; "
            f"projects={decision['distinct_projects']}; execution_started=false")
        return 0 if decision["status"] == "READY" else 3
    except (ExperimentGateError, OSError) as exc:
        print(f"experiment-gate: ERROR; {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
