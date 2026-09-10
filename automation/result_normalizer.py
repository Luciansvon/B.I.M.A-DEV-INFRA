"""Normalize bounded native test output without retaining raw logs."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


MAX_INPUT_BYTES = 1048576
MAX_SUITES = 100
MAX_DIAGNOSTICS = 50
MAX_MESSAGE_CHARS = 240
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
RUST_SUMMARY = re.compile(
    r"test result:\s*(?P<status>ok|FAILED)\.\s*"
    r"(?P<passed>\d+) passed;\s*(?P<failed>\d+) failed;\s*"
    r"(?P<ignored>\d+) ignored;\s*(?P<measured>\d+) measured;\s*"
    r"(?P<filtered>\d+) filtered out;",
    re.IGNORECASE,
)
TS_DIAGNOSTIC = re.compile(
    r"(?:##\[error\])?(?P<path>(?:[A-Za-z]:[\\/])?[^\r\n()]+\.(?:ts|tsx))"
    r"\((?P<line>\d+),(?P<column>\d+)\):\s*error\s+"
    r"(?P<code>TS\d+):\s*(?P<message>.+)$",
    re.IGNORECASE,
)
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*(?:bearer|basic)\s+)\S+"),
    re.compile(r"(?i)((?:token|password|secret|api[_-]?key)\s*[=:]\s*)\S+"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]


class NormalizationError(ValueError):
    """Input cannot be normalized under the supported contract."""


def _exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise NormalizationError(f"{label} fields do not match the contract")


def _string(value, label, maximum=256):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise NormalizationError(f"{label} is invalid")


def _identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise NormalizationError(f"{label} is invalid")


def _sha(value, label):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise NormalizationError(f"{label} must be SHA-256")


def _integer(value, label, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise NormalizationError(f"{label} is outside its allowed range")


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise NormalizationError("duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise NormalizationError("non-finite JSON number")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise NormalizationError("input is not strict UTF-8 JSON") from exc


def load_bytes(path):
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise NormalizationError("input must be a regular file of at most 1048576 bytes")
    return path.read_bytes()


def validate_request(value):
    _exact(value, {"schema", "project", "subject", "check", "adapter", "command",
                   "policy", "environment", "attempt", "exit_code", "sources"}, "request")
    if value["schema"] != "bima-normalization-request.v1":
        raise NormalizationError("unsupported request schema")
    _exact(value["project"], {"id", "repository"}, "project")
    _identifier(value["project"]["id"], "project id")
    _string(value["project"]["repository"], "repository")
    _exact(value["subject"], {"revision", "dirty"}, "subject")
    if not isinstance(value["subject"]["revision"], str) or not REVISION.fullmatch(value["subject"]["revision"]):
        raise NormalizationError("subject revision must be a full Git SHA")
    if type(value["subject"]["dirty"]) is not bool:
        raise NormalizationError("subject dirty must be boolean")
    _exact(value["check"], {"id", "required", "expected_tests"}, "check")
    _identifier(value["check"]["id"], "check id")
    if type(value["check"]["required"]) is not bool:
        raise NormalizationError("check required must be boolean")
    _integer(value["check"]["expected_tests"], "expected_tests", 1, 1000000)
    if value["adapter"] != "rust-libtest-text.v1":
        raise NormalizationError("unsupported adapter")
    for name in ("command", "policy"):
        _exact(value[name], {"id" if name == "command" else "revision", "sha256"}, name)
        _string(value[name]["id" if name == "command" else "revision"], f"{name} identity")
        _sha(value[name]["sha256"], f"{name} sha256")
    _exact(value["environment"], {"os", "arch", "toolchain"}, "environment")
    for field in ("os", "arch", "toolchain"):
        _string(value["environment"][field], f"environment {field}")
    _exact(value["attempt"], {"id", "sequence", "equivalence_key"}, "attempt")
    _identifier(value["attempt"]["id"], "attempt id")
    _integer(value["attempt"]["sequence"], "attempt sequence", 1, 100)
    _string(value["attempt"]["equivalence_key"], "equivalence_key", 128)
    _integer(value["exit_code"], "exit_code", 0, 255)
    _exact(value["sources"], {"native_output_sha256", "failure_log_sha256"}, "sources")
    _sha(value["sources"]["native_output_sha256"], "native_output_sha256")
    if value["sources"]["failure_log_sha256"] is not None:
        _sha(value["sources"]["failure_log_sha256"], "failure_log_sha256")
    return value


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def source_record(role, raw):
    return {"role": role, "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}


def parse_rust_summaries(text):
    summaries = []
    for match in RUST_SUMMARY.finditer(ANSI.sub("", text)):
        if len(summaries) >= MAX_SUITES:
            raise NormalizationError("native output contains too many test summaries")
        summaries.append({
            "status": match.group("status").lower(),
            "passed": int(match.group("passed")),
            "failed": int(match.group("failed")),
            "ignored": int(match.group("ignored")),
            "measured": int(match.group("measured")),
            "filtered_out": int(match.group("filtered")),
        })
    return summaries


def _sanitize(message):
    value = ANSI.sub("", message).replace("\x00", "").strip()
    for pattern in SECRET_PATTERNS:
        value = pattern.sub(lambda match: (match.group(1) if match.lastindex else "") + "[REDACTED]", value)
    return value[:MAX_MESSAGE_CHARS]


def _relative_source_path(value):
    normalized = value.replace("\\", "/").strip()
    positions = [position for marker in ("src/", "tests/")
                 if (position := normalized.lower().find(marker)) >= 0]
    if positions:
        normalized = normalized[min(positions):]
    normalized = re.sub(r"^[A-Za-z]:/", "", normalized).lstrip("/")
    if ".." in normalized.split("/") or not normalized:
        return "[unresolved-path]"
    return normalized[:256]


def parse_typescript_diagnostics(text):
    diagnostics = []
    for line in ANSI.sub("", text).splitlines():
        match = TS_DIAGNOSTIC.search(line)
        if not match:
            continue
        diagnostics.append({
            "tool": "typescript",
            "code": match.group("code").upper(),
            "path": _relative_source_path(match.group("path")),
            "line": int(match.group("line")),
            "column": int(match.group("column")),
            "message": _sanitize(match.group("message")),
        })
        if len(diagnostics) >= MAX_DIAGNOSTICS:
            break
    return diagnostics


def normalize(request, native_raw, failure_raw=None):
    validate_request(request)
    if len(native_raw) > MAX_INPUT_BYTES or (failure_raw is not None and len(failure_raw) > MAX_INPUT_BYTES):
        raise NormalizationError("native inputs exceed the byte limit")
    try:
        native_text = native_raw.decode("utf-8")
        failure_text = failure_raw.decode("utf-8") if failure_raw is not None else ""
    except UnicodeError as exc:
        raise NormalizationError("native inputs must be UTF-8") from exc
    native_hash = hashlib.sha256(native_raw).hexdigest()
    failure_hash = hashlib.sha256(failure_raw).hexdigest() if failure_raw is not None else None
    if native_hash != request["sources"]["native_output_sha256"]:
        raise NormalizationError("native output does not match the declared SHA-256")
    if failure_hash != request["sources"]["failure_log_sha256"]:
        raise NormalizationError("failure log presence or SHA-256 does not match the request")
    summaries = parse_rust_summaries(native_text)
    diagnostics = parse_typescript_diagnostics(failure_text)
    counts = {
        field: sum(suite[field] for suite in summaries)
        for field in ("passed", "failed", "ignored", "measured", "filtered_out")
    }
    observed = counts["passed"] + counts["failed"] + counts["ignored"]
    expected = request["check"]["expected_tests"]
    exit_code = request["exit_code"]
    if not summaries:
        outcome, verdict, reason = "unknown", "UNKNOWN", "MISSING_TEST_SUMMARY"
    elif any(suite["status"] == "failed" for suite in summaries) or counts["failed"] > 0:
        if exit_code == 0:
            outcome, verdict, reason = "unknown", "UNKNOWN", "EXIT_SUMMARY_DISAGREE"
        else:
            outcome, verdict, reason = "fail", "FAIL", "TEST_FAILURE_REPORTED"
    elif exit_code != 0:
        outcome, verdict, reason = "unknown", "UNKNOWN", "NONZERO_EXIT_WITHOUT_TEST_FAILURE"
    elif observed != expected:
        outcome, verdict, reason = "unknown", "UNKNOWN", "EXPECTED_TEST_COUNT_MISMATCH"
    else:
        outcome, verdict, reason = "pass", "PASS", "ALL_EXPECTED_TESTS_PASSED"
    sources = [source_record("native-test-output", native_raw)]
    if failure_raw is not None:
        sources.append(source_record("failure-log", failure_raw))
    return {
        "schema": "bima-verification-result.v2",
        "verdict": verdict,
        "identity": {
            "project_id": request["project"]["id"],
            "repository": request["project"]["repository"],
            "subject_revision": request["subject"]["revision"],
            "subject_dirty": request["subject"]["dirty"],
            "check_id": request["check"]["id"],
        },
        "adapter": request["adapter"],
        "command": request["command"],
        "policy": request["policy"],
        "environment": request["environment"],
        "attempt": request["attempt"],
        "execution": {"lifecycle": "completed", "exit_code": exit_code},
        "applicability": "required" if request["check"]["required"] else "optional",
        "outcome": {
            "value": outcome,
            "reason_code": reason,
            "expected_tests": expected,
            "observed_tests": observed,
            "counts": counts,
            "suites": summaries,
        },
        "stability": {"value": "unassessed", "equivalence_key": request["attempt"]["equivalence_key"]},
        "sources": sources,
        "diagnostics": diagnostics,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--native-output", type=Path, required=True)
    parser.add_argument("--failure-log", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        request = strict_json(load_bytes(args.request))
        native_raw = load_bytes(args.native_output)
        failure_raw = load_bytes(args.failure_log) if args.failure_log else None
        result = normalize(request, native_raw, failure_raw)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "result.json").write_bytes(canonical_bytes(result))
        print(f"result-normalizer: {result['verdict']}; reason={result['outcome']['reason_code']}; diagnostics={len(result['diagnostics'])}")
        return {"PASS": 0, "FAIL": 1, "UNKNOWN": 2, "BLOCKED": 3}[result["verdict"]]
    except (NormalizationError, OSError) as exc:
        print(f"result-normalizer: ERROR; {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
