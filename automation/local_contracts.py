"""Run checked-in fixture contracts that need only the Python standard library."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
TIMEOUT_SECONDS = 20


class ContractError(RuntimeError):
    """A checked-in fixture did not produce its contracted result."""


def expect(condition, message):
    if not condition:
        raise ContractError(message)


def expect_equal(actual, expected, label):
    expect(actual == expected, f"{label}: expected {expected!r}, got {actual!r}")


def canonical(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(module, *arguments, expect_code=0):
    command = [sys.executable, "-I", str(ROOT / "automation" / module),
               *[str(argument) for argument in arguments]]
    try:
        completed = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True,
            timeout=TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractError(f"{module} could not run: {exc}") from exc
    if completed.returncode != expect_code:
        raise ContractError(
            f"{module} exited {completed.returncode}, expected {expect_code}; "
            f"stdout={completed.stdout.strip()!r}; "
            f"stderr={completed.stderr.strip()!r}")
    return completed


def check_failure_records(temporary):
    source_path = ROOT / "failure-records" / "records.json"
    output = temporary / "failure-records"
    completed = run(
        "failure_records.py", "--input", source_path, "--output", output)
    source = load_json(source_path)
    summary = load_json(output / "summary.json")
    expected = sum(
        record["case_kind"] == "real" and record["status"] == "ACTIVE"
        for record in source["records"])
    expect_equal(summary["total_records"], len(source["records"]),
                 "failure-records total")
    expect_equal(summary["real_verified_records"], expected,
                 "failure-records real_verified")
    expect(f"real_verified={expected}" in completed.stdout,
           "failure-records stdout does not report the real count")
    return f"real_verified={expected}"


def check_result_normalizer(temporary):
    output = temporary / "result-normalization"
    config_path = FIXTURES / "result-normalizer" / "config-pass.json"
    config = load_json(config_path)
    run(
        "result_normalizer.py",
        "--config", config_path,
        "--subject-revision", "0" * 40,
        "--subject-dirty", "false",
        "--attempt-id", "local-contracts",
        "--attempt-sequence", "1",
        "--exit-code", "0",
        "--native-output", FIXTURES / "result-normalizer" / "rust-pass.log",
        "--output", output)
    result = load_json(output / "result.json")
    expect_equal(result["verdict"], "PASS", "normalizer verdict")
    expect_equal(result["outcome"]["reason_code"],
                 "ALL_EXPECTED_TESTS_PASSED", "normalizer reason")
    expect_equal(result["outcome"]["expected_tests"],
                 result["outcome"]["observed_tests"], "normalizer test counts")
    return output / "result.json", config


def check_verification_aggregate(temporary, result_path, config):
    result = load_json(result_path)
    plan_path = FIXTURES / "verification-aggregate" / "plan-pass.json"
    plan = load_json(plan_path)
    fixture_matches = (
        plan["project"] == config["project"]
        and plan["required_checks"] == [config["check"]["id"]]
        and plan["optional_checks"] == []
        and plan["subject"] == {
            "revision": result["identity"]["subject_revision"],
            "dirty": result["identity"]["subject_dirty"]}
        and plan["policy"] == result["policy"])
    if not fixture_matches:
        plan = {
            "schema": "bima-verification-plan.v1",
            "aggregate_id": "local-contracts",
            "project": dict(config["project"]),
            "subject": {
                "revision": result["identity"]["subject_revision"],
                "dirty": result["identity"]["subject_dirty"]},
            "policy": dict(result["policy"]),
            "required_checks": [config["check"]["id"]],
            "optional_checks": []}
        plan_path = temporary / "verification-plan" / "plan.json"
        write_json(plan_path, plan)
    output = temporary / "verification-aggregate"
    run(
        "verification_aggregate.py",
        "--plan", plan_path, "--result", result_path, "--output", output)
    aggregate = load_json(output / "aggregate.json")
    required = aggregate["counts"]["required"]
    expect_equal(aggregate["verdict"], "PASS", "aggregate verdict")
    expect_equal(aggregate["reason_code"], "ALL_REQUIRED_CHECKS_PASSED",
                 "aggregate reason")
    expect_equal({key: required[key] for key in ("declared", "reported", "pass")},
                 {"declared": 1, "reported": 1, "pass": 1},
                 "aggregate required counts")
    expect_equal(aggregate["unresolved_required"], [],
                 "aggregate unresolved required")
    return f"required={required['reported']}/{required['declared']}"


def check_artifact_identity(temporary):
    root = temporary / "artifact-root"
    relative = ".artifacts/local-contract/application.bin"
    artifact = root / relative
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"BIMA local contract artifact fixture v1\x00")
    request = load_json(FIXTURES / "artifact-identity" / "request.json")
    request["artifacts"][0]["path"] = relative
    request_path = temporary / "artifact-request" / "request.json"
    write_json(request_path, request)
    create_output = temporary / "artifact-identity-create"
    run(
        "artifact_identity.py", "create",
        "--request", request_path, "--root", root, "--output", create_output)
    manifest_path = create_output / "manifest.json"
    verify_output = temporary / "artifact-identity-verify"
    run(
        "artifact_identity.py", "verify",
        "--manifest", manifest_path, "--root", root, "--output", verify_output)
    manifest = load_json(manifest_path)
    verification = load_json(verify_output / "verification.json")
    expect_equal([item["path"] for item in manifest["artifacts"]],
                 [relative], "artifact manifest paths")
    expect_equal(verification["verdict"], "PASS", "artifact verdict")
    expect_equal(verification["reason_code"], "ALL_ARTIFACTS_MATCH",
                 "artifact reason")
    expect_equal(verification["counts"],
                 {"changed": 0, "declared": 1, "matched": 1,
                  "missing": 0, "unsafe": 0}, "artifact counts")
    expect_equal(verification["manifest_sha256"],
                 hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                 "artifact manifest digest")
    expect_equal(verification["unresolved_artifacts"], [],
                 "artifact unresolved")
    return "matched=1/1"


def check_known_failure(temporary):
    request = load_json(FIXTURES / "result-normalizer" / "request-pass.json")
    request["project"] = {
        "id": "dev-infra-fixture",
        "repository": "Luciansvon/B.I.M.A-DEV-INFRA"}
    request["check"]["id"] = "fixture-rust-tests"
    request["environment"]["toolchain"] = "rust-fixture-v1"
    request["exit_code"] = 1
    native = (b"test result: FAILED. 28 passed; 1 failed; 0 ignored; "
              b"0 measured; 0 filtered out;\n")
    native_path = temporary / "known-failure" / "native.log"
    native_path.parent.mkdir(parents=True, exist_ok=True)
    native_path.write_bytes(native)
    failure_path = (
        FIXTURES / "known-failure-registry" / "same-attempt-diagnostic.log")
    request["sources"] = {
        "native_output_sha256": hashlib.sha256(native).hexdigest(),
        "failure_log_sha256": hashlib.sha256(
            failure_path.read_bytes()).hexdigest()}
    request_path = temporary / "known-failure" / "request.json"
    write_json(request_path, request)
    result_dir = temporary / "known-failure" / "result"
    run(
        "result_normalizer.py",
        "--request", request_path,
        "--native-output", native_path,
        "--failure-log", failure_path,
        "--output", result_dir,
        expect_code=1)
    result = load_json(result_dir / "result.json")
    expect_equal(result["verdict"], "FAIL", "known-failure result verdict")
    expect_equal(result["outcome"]["reason_code"], "TEST_FAILURE_REPORTED",
                 "known-failure result reason")
    expect_equal([diagnostic["code"] for diagnostic in result["diagnostics"]],
                 ["TS9001"], "known-failure diagnostics")
    classification_dir = temporary / "known-failure" / "classification"
    run(
        "known_failure_registry.py",
        "--result", result_dir / "result.json",
        "--registry", FIXTURES / "known-failure-registry" / "registry.json",
        "--as-of", "2026-09-15T00:00:00Z",
        "--output", classification_dir)
    classification = load_json(classification_dir / "classification.json")
    expect_equal(classification["classification"], "known_failure",
                 "known-failure classification")
    expect_equal(classification["route"], "machine", "known-failure route")
    expect(classification["automatic_retry_allowed"] is False,
           "known-failure registry authorized an automatic retry")
    expect_equal(classification["match"]["entry_id"],
                 "dev-infra-synthetic-known-failure-2026-09",
                 "known-failure entry")
    return "classification=known_failure; route=machine"


def check_failure_memory(temporary):
    database = temporary / "failure-memory.sqlite3"
    report_path = temporary / "failure-memory" / "report.json"
    completed = run(
        "failure_memory.py",
        "--input", ROOT / "failure-records" / "records.json",
        "--database", database,
        "--repository-root", ROOT,
        "--report", report_path,
        expect_code=3)
    report = load_json(report_path)
    expect_equal(report["status"], "BLOCKED", "failure-memory status")
    expect_equal(report["reason_code"], "INSUFFICIENT_REAL_CASES",
                 "failure-memory reason")
    expect(report["real_verified_records"] < report["minimum_real_cases"],
           "failure memory blocked despite meeting the threshold")
    expect(report["database_created"] is False and not database.exists(),
           "failure memory created a database while blocked")
    expect("BLOCKED" in completed.stdout,
           "failure memory stdout does not report the blocked state")
    return (f"real_verified={report['real_verified_records']}/"
            f"{report['minimum_real_cases']}; database_created=false")


def check_failure_memory_benchmark(temporary):
    database = temporary / "failure-memory-benchmark.sqlite3"
    report_path = temporary / "failure-memory-benchmark" / "report.json"
    run(
        "failure_memory_benchmark.py",
        "--records", ROOT / "failure-records" / "records.json",
        "--queries", ROOT / "benchmarks" / "failure-memory" / "held-out.json",
        "--database", database,
        "--repository-root", ROOT,
        "--report", report_path,
        "--bind-record-set",
        expect_code=3)
    report = load_json(report_path)
    expect_equal(report["status"], "BLOCKED", "benchmark status")
    expect_equal(report["reason_code"], "INSUFFICIENT_REAL_CASES",
                 "benchmark reason")
    expect(report["metrics"] is None and report["database_created"] is False,
           "benchmark reported metrics or a database while blocked")
    expect(not database.exists(),
           "benchmark created a database while blocked")
    return "BLOCKED; metrics=null; database_created=false"


def check_workflow_catalog(temporary):
    completed = run("workflow_catalog.py")
    catalog = load_json(ROOT / "catalog" / "workflows.json")
    count = len(catalog["workflows"])
    expect(f"workflows={count}" in completed.stdout,
           "workflow catalog stdout does not report the entry count")
    return f"workflows={count}"


def check_fleet_dispatch(temporary):
    output = temporary / "fleet"
    completed = run("fleet_dispatch.py", "--output", output)
    fleet = load_json(ROOT / "fleet" / "repos.json")
    evidence = load_json(output / "evidence.json")
    expect_equal(evidence["mode"], "dry-run", "fleet mode")
    expect_equal([item["repository"] for item in evidence["dispatches"]],
                 [entry["repository"] for entry in fleet["repositories"]],
                 "fleet repositories")
    expect(all(item["status"] == "planned" and item["run_id"] is None
               for item in evidence["dispatches"]),
           "fleet dry-run dispatched a workflow or resolved a run")
    expect("mode=dry-run" in completed.stdout,
           "fleet stdout does not report the dry-run mode")
    return f"mode=dry-run; repositories={len(evidence['dispatches'])}"


def check_experiment_gate(temporary):
    output = temporary / "experiment-gate"
    completed = run(
        "experiment_gate.py",
        "--request", FIXTURES / "experiment-gate" / "request-one-project.json",
        "--output", output,
        expect_code=3)
    decision = load_json(output / "decision.json")
    expect_equal(decision["status"], "BLOCKED", "experiment status")
    expect_equal(decision["reason_code"], "INSUFFICIENT_CROSS_PROJECT_DEMAND",
                 "experiment reason")
    expect(decision["execution_started"] is False,
           "experiment gate started execution while blocked")
    expect("BLOCKED" in completed.stdout,
           "experiment stdout does not report the blocked state")
    return "BLOCKED; execution_started=false"


def main():
    checks = []
    try:
        with tempfile.TemporaryDirectory(
                prefix="bima-local-contracts-") as temporary:
            temporary_path = Path(temporary)
            detail = check_failure_records(temporary_path)
            checks.append("failure-records")
            print(f"local-contracts: failure-records: pass; {detail}")
            result_path, config = check_result_normalizer(temporary_path)
            checks.append("result-normalizer")
            print("local-contracts: result-normalizer: pass; "
                  "PASS/ALL_EXPECTED_TESTS_PASSED")
            detail = check_verification_aggregate(
                temporary_path, result_path, config)
            checks.append("verification-aggregate")
            print(f"local-contracts: verification-aggregate: pass; {detail}")
            detail = check_artifact_identity(temporary_path)
            checks.append("artifact-identity")
            print(f"local-contracts: artifact-identity: pass; {detail}")
            detail = check_known_failure(temporary_path)
            checks.append("known-failure-registry")
            print(f"local-contracts: known-failure-registry: pass; {detail}")
            detail = check_failure_memory(temporary_path)
            checks.append("failure-memory")
            print(f"local-contracts: failure-memory: pass; {detail}")
            detail = check_failure_memory_benchmark(temporary_path)
            checks.append("failure-memory-benchmark")
            print(
                f"local-contracts: failure-memory-benchmark: pass; {detail}")
            detail = check_experiment_gate(temporary_path)
            checks.append("experiment-gate")
            print(f"local-contracts: experiment-gate: pass; {detail}")
            detail = check_workflow_catalog(temporary_path)
            checks.append("workflow-catalog")
            print(f"local-contracts: workflow-catalog: pass; {detail}")
            detail = check_fleet_dispatch(temporary_path)
            checks.append("fleet-dispatch")
            print(f"local-contracts: fleet-dispatch: pass; {detail}")
    except (ContractError, OSError, json.JSONDecodeError, KeyError,
            TypeError) as exc:
        print(f"local-contracts: FAIL; {exc}", file=sys.stderr)
        return 1
    print(f"local-contracts: PASS; contracts={len(checks)}; failed=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
