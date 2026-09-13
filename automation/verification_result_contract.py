"""Shared strict validator for bima-verification-result.v2."""

import re


MAX_INPUT_BYTES = 1048576
MAX_DIAGNOSTICS = 50
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
RESULT_FIELDS = {
    "schema", "verdict", "identity", "adapter", "command", "policy",
    "environment", "attempt", "execution", "applicability", "outcome",
    "stability", "sources", "diagnostics",
}


class VerificationResultError(ValueError):
    """A v2 verification result violates its strict contract."""


def _exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise VerificationResultError(f"{label} fields do not match the contract")


def _string(value, label, maximum=512):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise VerificationResultError(f"{label} is invalid")


def _identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise VerificationResultError(f"{label} is invalid")


def _sha(value, label):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise VerificationResultError(f"{label} must be SHA-256")


def _nonnegative(value, label):
    if type(value) is not int or value < 0:
        raise VerificationResultError(f"{label} must be a nonnegative integer")


def validate_result(value):
    _exact(value, RESULT_FIELDS, "result")
    if value["schema"] != "bima-verification-result.v2":
        raise VerificationResultError("unsupported result schema")
    if value["verdict"] not in {"PASS", "FAIL", "UNKNOWN", "BLOCKED"}:
        raise VerificationResultError("result verdict is invalid")
    _exact(value["identity"], {"project_id", "repository", "subject_revision",
                               "subject_dirty", "check_id"}, "result identity")
    _string(value["identity"]["project_id"], "result project id")
    _string(value["identity"]["repository"], "result repository")
    if not isinstance(value["identity"]["subject_revision"], str) or not REVISION.fullmatch(value["identity"]["subject_revision"]):
        raise VerificationResultError("result subject revision must be a full Git SHA")
    if type(value["identity"]["subject_dirty"]) is not bool:
        raise VerificationResultError("result subject dirty must be boolean")
    _string(value["identity"]["check_id"], "result check id")
    if value["adapter"] != "rust-libtest-text.v1":
        raise VerificationResultError("unsupported result adapter")
    _exact(value["command"], {"id", "sha256"}, "result command")
    _string(value["command"]["id"], "result command id")
    _sha(value["command"]["sha256"], "result command sha256")
    _exact(value["policy"], {"revision", "sha256"}, "result policy")
    _string(value["policy"]["revision"], "result policy revision")
    _sha(value["policy"]["sha256"], "result policy sha256")
    _exact(value["environment"], {"os", "arch", "toolchain"}, "result environment")
    for field in ("os", "arch", "toolchain"):
        _string(value["environment"][field], f"result environment {field}")
    _exact(value["attempt"], {"id", "sequence", "equivalence_key"}, "result attempt")
    _identifier(value["attempt"]["id"], "result attempt id")
    if type(value["attempt"]["sequence"]) is not int or not 1 <= value["attempt"]["sequence"] <= 100:
        raise VerificationResultError("result attempt sequence is invalid")
    _string(value["attempt"]["equivalence_key"], "result equivalence key", 128)
    _exact(value["execution"], {"lifecycle", "exit_code"}, "result execution")
    if value["execution"]["lifecycle"] != "completed":
        raise VerificationResultError("unsupported result lifecycle")
    if type(value["execution"]["exit_code"]) is not int or not 0 <= value["execution"]["exit_code"] <= 255:
        raise VerificationResultError("result exit code is invalid")
    if value["applicability"] not in {"required", "optional"}:
        raise VerificationResultError("result applicability is invalid")
    _exact(value["outcome"], {"value", "reason_code", "expected_tests",
                              "observed_tests", "counts", "suites"}, "result outcome")
    if value["outcome"]["value"] not in {"pass", "fail", "unknown", "not_run"}:
        raise VerificationResultError("result outcome is invalid")
    expected_outcomes = {"PASS": "pass", "FAIL": "fail", "UNKNOWN": "unknown"}
    if value["verdict"] in expected_outcomes and value["outcome"]["value"] != expected_outcomes[value["verdict"]]:
        raise VerificationResultError("result verdict and outcome disagree")
    _string(value["outcome"]["reason_code"], "result reason code", 128)
    if type(value["outcome"]["expected_tests"]) is not int or value["outcome"]["expected_tests"] < 1:
        raise VerificationResultError("result expected tests must be positive")
    _nonnegative(value["outcome"]["observed_tests"], "result observed tests")
    _exact(value["outcome"]["counts"], {"passed", "failed", "ignored",
                                        "measured", "filtered_out"}, "result counts")
    for field in ("passed", "failed", "ignored", "measured", "filtered_out"):
        _nonnegative(value["outcome"]["counts"][field], f"result count {field}")
    if not isinstance(value["outcome"]["suites"], list) or len(value["outcome"]["suites"]) > 100:
        raise VerificationResultError("result suites are invalid")
    for index, suite in enumerate(value["outcome"]["suites"]):
        _exact(suite, {"status", "passed", "failed", "ignored", "measured",
                       "filtered_out"}, f"result suite {index}")
        if suite["status"] not in {"ok", "failed"}:
            raise VerificationResultError("result suite status is invalid")
        for field in ("passed", "failed", "ignored", "measured", "filtered_out"):
            _nonnegative(suite[field], f"result suite {index} {field}")
        if (suite["status"] == "failed") != (suite["failed"] > 0):
            raise VerificationResultError("result suite status and failed count disagree")
    calculated_counts = {
        field: sum(suite[field] for suite in value["outcome"]["suites"])
        for field in ("passed", "failed", "ignored", "measured", "filtered_out")
    }
    if value["outcome"]["counts"] != calculated_counts:
        raise VerificationResultError("result counts do not equal the retained suites")
    calculated_observed = (
        calculated_counts["passed"] + calculated_counts["failed"]
        + calculated_counts["ignored"]
    )
    if value["outcome"]["observed_tests"] != calculated_observed:
        raise VerificationResultError("result observed tests are inconsistent")
    if value["verdict"] == "PASS" and (
            calculated_counts["failed"] != 0
            or value["execution"]["exit_code"] != 0
            or value["outcome"]["expected_tests"] != calculated_observed):
        raise VerificationResultError("PASS result does not satisfy its declared expectation")
    if value["verdict"] == "FAIL" and (
            calculated_counts["failed"] == 0
            or value["execution"]["exit_code"] == 0):
        raise VerificationResultError("FAIL result lacks failed tests or a nonzero exit")
    _exact(value["stability"], {"value", "equivalence_key"}, "result stability")
    if value["stability"]["value"] not in {"unassessed", "consistent_observed", "flaky"}:
        raise VerificationResultError("result stability is invalid")
    _string(value["stability"]["equivalence_key"], "result stability key", 128)
    if value["stability"]["equivalence_key"] != value["attempt"]["equivalence_key"]:
        raise VerificationResultError("result stability and attempt keys disagree")
    if not isinstance(value["sources"], list) or not 1 <= len(value["sources"]) <= 2:
        raise VerificationResultError("result sources are invalid")
    source_roles = set()
    for index, source in enumerate(value["sources"]):
        _exact(source, {"role", "sha256", "size_bytes"}, f"result source {index}")
        if source["role"] not in {"native-test-output", "failure-log"} or source["role"] in source_roles:
            raise VerificationResultError("result source role is invalid or duplicated")
        source_roles.add(source["role"])
        _sha(source["sha256"], f"result source {index} sha256")
        _nonnegative(source["size_bytes"], f"result source {index} size")
        if source["size_bytes"] > MAX_INPUT_BYTES:
            raise VerificationResultError("result source exceeds the byte limit")
    if "native-test-output" not in source_roles:
        raise VerificationResultError("result lacks native test output identity")
    if not isinstance(value["diagnostics"], list) or len(value["diagnostics"]) > MAX_DIAGNOSTICS:
        raise VerificationResultError("result diagnostics are invalid")
    for index, diagnostic in enumerate(value["diagnostics"]):
        _exact(diagnostic, {"tool", "code", "path", "line", "column", "message"},
               f"result diagnostic {index}")
        if diagnostic["tool"] != "typescript" or not re.fullmatch(r"TS\d+", diagnostic["code"]):
            raise VerificationResultError("result diagnostic tool or code is invalid")
        _string(diagnostic["path"], f"result diagnostic {index} path", 256)
        _string(diagnostic["message"], f"result diagnostic {index} message", 240)
        for field in ("line", "column"):
            if type(diagnostic[field]) is not int or diagnostic[field] < 1:
                raise VerificationResultError(f"result diagnostic {index} {field} is invalid")
    return value
