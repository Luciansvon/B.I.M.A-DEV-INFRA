"""Aggregate declared verification results without executing project commands."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


MAX_INPUT_BYTES = 1048576
MAX_CHECKS = 64
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _load_result_contract():
    path = Path(__file__).with_name("verification_result_contract.py")
    spec = importlib.util.spec_from_file_location("bima_verification_result_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("verification result contract cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


result_contract = _load_result_contract()


class AggregateError(ValueError):
    """Input cannot be aggregated under the supported contract."""


def _exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise AggregateError(f"{label} fields do not match the contract")


def _string(value, label, maximum=256):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise AggregateError(f"{label} is invalid")


def _identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise AggregateError(f"{label} is invalid")


def _sha(value, label):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise AggregateError(f"{label} must be SHA-256")


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise AggregateError("duplicate JSON key")
            value[key] = item
        return value

    def constant(_):
        raise AggregateError("non-finite JSON number")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise AggregateError("input is not strict UTF-8 JSON") from exc


def load_json(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise AggregateError("input must be a regular file of at most 1048576 bytes")
    return strict_json(path.read_bytes())


def _check_ids(value, label, allow_empty):
    if not isinstance(value, list) or len(value) > MAX_CHECKS:
        raise AggregateError(f"{label} must be a bounded list")
    if not allow_empty and not value:
        raise AggregateError(f"{label} cannot be empty")
    for check_id in value:
        _identifier(check_id, f"{label} entry")
    if value != sorted(set(value)):
        raise AggregateError(f"{label} must be unique and sorted")


def validate_plan(value):
    _exact(value, {"schema", "aggregate_id", "project", "subject", "policy",
                   "required_checks", "optional_checks"}, "plan")
    if value["schema"] != "bima-verification-plan.v1":
        raise AggregateError("unsupported plan schema")
    _identifier(value["aggregate_id"], "aggregate id")
    _exact(value["project"], {"id", "repository"}, "plan project")
    _identifier(value["project"]["id"], "plan project id")
    _string(value["project"]["repository"], "plan repository")
    _exact(value["subject"], {"revision", "dirty"}, "plan subject")
    if not isinstance(value["subject"]["revision"], str) or not REVISION.fullmatch(value["subject"]["revision"]):
        raise AggregateError("plan subject revision must be a full Git SHA")
    if type(value["subject"]["dirty"]) is not bool:
        raise AggregateError("plan subject dirty must be boolean")
    _exact(value["policy"], {"revision", "sha256"}, "plan policy")
    _string(value["policy"]["revision"], "plan policy revision")
    _sha(value["policy"]["sha256"], "plan policy sha256")
    _check_ids(value["required_checks"], "required checks", False)
    _check_ids(value["optional_checks"], "optional checks", True)
    combined = value["required_checks"] + value["optional_checks"]
    if len(combined) > MAX_CHECKS or len(combined) != len(set(combined)):
        raise AggregateError("required and optional checks must be disjoint and bounded")
    return value


def validate_result(value):
    try:
        result_contract.validate_result(value)
    except result_contract.VerificationResultError as exc:
        raise AggregateError(str(exc)) from exc
    if value["verdict"] == "BLOCKED" and (
            value["outcome"]["value"] != "not_run"
            or value["outcome"]["observed_tests"] != 0
            or value["outcome"]["suites"]):
        raise AggregateError("BLOCKED result must not claim executed tests")
    return value


def _empty_counts(declared):
    return {
        "declared": declared, "reported": 0, "missing": declared,
        "pass": 0, "fail": 0, "unknown": 0, "blocked": 0, "flaky": 0,
    }


def aggregate(plan, results):
    validate_plan(plan)
    if not isinstance(results, list) or len(results) > MAX_CHECKS:
        raise AggregateError("results must contain at most 64 entries")
    declared = set(plan["required_checks"] + plan["optional_checks"])
    by_check = {}
    for result in results:
        validate_result(result)
        identity = result["identity"]
        check_id = identity["check_id"]
        if check_id not in declared:
            raise AggregateError("result check is not declared by the plan")
        if check_id in by_check:
            raise AggregateError("result check ids must be unique")
        if identity["project_id"] != plan["project"]["id"] or identity["repository"] != plan["project"]["repository"]:
            raise AggregateError("result project does not match the plan")
        if result["policy"] != plan["policy"]:
            raise AggregateError("result policy does not match the plan")
        result_subject = {
            "revision": identity["subject_revision"],
            "dirty": identity["subject_dirty"],
        }
        if result_subject != plan["subject"]:
            raise AggregateError("result subject does not match the plan")
        expected_applicability = (
            "required" if check_id in plan["required_checks"] else "optional"
        )
        if result["applicability"] != expected_applicability:
            raise AggregateError("result applicability does not match the plan")
        by_check[check_id] = result

    counts = {
        "required": _empty_counts(len(plan["required_checks"])),
        "optional": _empty_counts(len(plan["optional_checks"])),
    }
    checks = []
    unresolved_required = []
    optional_non_pass = []
    for applicability, ids in (("required", plan["required_checks"]),
                               ("optional", plan["optional_checks"])):
        bucket = counts[applicability]
        for check_id in ids:
            result = by_check.get(check_id)
            if result is None:
                check = {
                    "check_id": check_id,
                    "applicability": applicability,
                    "state": "missing",
                    "verdict": "UNKNOWN",
                    "reason_code": "RESULT_MISSING",
                    "stability": "unassessed",
                    "result_sha256": None,
                }
                if applicability == "required":
                    unresolved_required.append(check_id)
                else:
                    optional_non_pass.append(check_id)
            else:
                verdict = result["verdict"]
                stability = result["stability"]["value"]
                check = {
                    "check_id": check_id,
                    "applicability": applicability,
                    "state": "reported",
                    "verdict": verdict,
                    "reason_code": result["outcome"]["reason_code"],
                    "stability": stability,
                    "result_sha256": hashlib.sha256(canonical_bytes(result)).hexdigest(),
                }
                bucket[verdict.lower()] += 1
                if stability == "flaky":
                    bucket["flaky"] += 1
                if applicability == "required" and (verdict != "PASS" or stability == "flaky"):
                    unresolved_required.append(check_id)
                if applicability == "optional" and (verdict != "PASS" or stability == "flaky"):
                    optional_non_pass.append(check_id)
                bucket["reported"] += 1
                bucket["missing"] -= 1
            checks.append(check)

    required = counts["required"]
    if required["fail"]:
        verdict, reason = "FAIL", "REQUIRED_CHECK_FAILED"
    elif required["blocked"]:
        verdict, reason = "BLOCKED", "REQUIRED_CHECK_BLOCKED"
    elif required["missing"]:
        verdict, reason = "UNKNOWN", "REQUIRED_EVIDENCE_MISSING"
    elif required["unknown"]:
        verdict, reason = "UNKNOWN", "REQUIRED_CHECK_UNKNOWN"
    elif required["flaky"]:
        verdict, reason = "UNKNOWN", "REQUIRED_CHECK_FLAKY"
    else:
        verdict, reason = "PASS", "ALL_REQUIRED_CHECKS_PASSED"

    return {
        "schema": "bima-verification-aggregate.v1",
        "verdict": verdict,
        "reason_code": reason,
        "identity": {
            "aggregate_id": plan["aggregate_id"],
            "project_id": plan["project"]["id"],
            "repository": plan["project"]["repository"],
            "subject_revision": plan["subject"]["revision"],
            "subject_dirty": plan["subject"]["dirty"],
        },
        "policy": dict(plan["policy"]),
        "plan_sha256": hashlib.sha256(canonical_bytes(plan)).hexdigest(),
        "checks": checks,
        "counts": counts,
        "unresolved_required": sorted(unresolved_required),
        "optional_non_pass": sorted(optional_non_pass),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--result", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = aggregate(load_json(args.plan), [load_json(path) for path in args.result])
        if args.output.is_symlink():
            raise AggregateError("output directory cannot be a symlink")
        args.output.mkdir(parents=True, exist_ok=True)
        if not args.output.is_dir():
            raise AggregateError("output must be a directory")
        destination = args.output / "aggregate.json"
        if destination.exists() or destination.is_symlink():
            destination.unlink()
        destination.write_bytes(canonical_bytes(report))
        print(
            "verification-aggregate: "
            f"{report['verdict']}; reason={report['reason_code']}; "
            f"required={report['counts']['required']['reported']}/"
            f"{report['counts']['required']['declared']}"
        )
        return {"PASS": 0, "FAIL": 1, "UNKNOWN": 2, "BLOCKED": 3}[report["verdict"]]
    except (AggregateError, OSError) as exc:
        print(f"verification-aggregate: ERROR; {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
