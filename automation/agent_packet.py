"""Build a bounded routing packet from non-pass canonical evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


MAX_INPUT_BYTES = 1048576
MAX_RELEVANT_EVIDENCE = 20
MAX_AFFECTED_PATHS = 20
MAX_CODE_CHARS = 64
MAX_PATH_CHARS = 512
MAX_MESSAGE_CHARS = 512
OWNED_OUTPUTS = ("packet.json", "packet.sha256")
TOP_FIELDS = {"schema", "status", "subject", "policy", "toolchain", "checks"}
SUBJECT_FIELDS = {"revision", "dirty"}
POLICY_FIELDS = {"sha256"}
CHECK_FIELDS = {"id", "status", "metrics", "findings"}
METRIC_FIELDS = {"files_checked", "local_links_checked", "findings_count"}
FINDING_FIELDS = {"code", "path", "line", "message"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("non-finite JSON number")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2,
                       sort_keys=True) + "\n").encode("utf-8")


def nonnegative_integer(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def validate_canonical(value):
    if not isinstance(value, dict) or set(value) != TOP_FIELDS:
        raise ValueError("unsupported canonical evidence fields")
    if value["schema"] != "bima-evidence.v1":
        raise ValueError("unsupported canonical evidence schema")
    if value["status"] not in {"pass", "fail", "error"}:
        raise ValueError("unsupported status")

    subject = value["subject"]
    if not isinstance(subject, dict) or set(subject) != SUBJECT_FIELDS:
        raise ValueError("unsupported subject fields")
    if subject["revision"] is not None and (
            not isinstance(subject["revision"], str)
            or not REVISION.fullmatch(subject["revision"])):
        raise ValueError("invalid revision")
    if subject["dirty"] is not None and type(subject["dirty"]) is not bool:
        raise ValueError("dirty must be boolean or null")

    policy = value["policy"]
    if not isinstance(policy, dict) or set(policy) != POLICY_FIELDS:
        raise ValueError("unsupported policy fields")
    if policy["sha256"] is not None and (
            not isinstance(policy["sha256"], str)
            or not SHA256.fullmatch(policy["sha256"])):
        raise ValueError("invalid policy SHA-256")

    if value["status"] in {"pass", "fail"} and (
            subject["revision"] is None or subject["dirty"] is None):
        raise ValueError("completed audit requires revision and dirty state")

    toolchain = value["toolchain"]
    if not isinstance(toolchain, list) or len(toolchain) != 3:
        raise ValueError("repository-audit evidence requires three tools")
    for tool in toolchain:
        if not isinstance(tool, dict) or set(tool) not in (
                {"name", "version"}, {"name", "sha256"}):
            raise ValueError("unsupported toolchain fields")
        if not isinstance(tool["name"], str) or not tool["name"]:
            raise ValueError("tool name must be a non-empty string")
        if "version" in tool and (
                not isinstance(tool["version"], str) or not tool["version"]):
            raise ValueError("tool version must be a non-empty string")
        if "sha256" in tool and (
                not isinstance(tool["sha256"], str)
                or not SHA256.fullmatch(tool["sha256"])):
            raise ValueError("invalid tool SHA-256")
    expected_tools = (
        ("canonical-evidence", "sha256"),
        ("python", "version"),
        ("repository-audit", "sha256"),
    )
    if tuple((tool["name"], "sha256" if "sha256" in tool else "version")
             for tool in toolchain) != expected_tools:
        raise ValueError("unsupported repository-audit toolchain")

    checks = value["checks"]
    if not isinstance(checks, list) or len(checks) != 1:
        raise ValueError("repository-audit evidence requires exactly one check")
    check = checks[0]
    if not isinstance(check, dict) or set(check) != CHECK_FIELDS:
        raise ValueError("unsupported check fields")
    if check["id"] != "repository-audit":
        raise ValueError("unsupported check")
    if check["status"] != value["status"]:
        raise ValueError("check status does not match envelope status")
    metrics = check["metrics"]
    if not isinstance(metrics, dict) or set(metrics) != METRIC_FIELDS:
        raise ValueError("unsupported metric fields")
    for name in METRIC_FIELDS:
        nonnegative_integer(metrics[name], name)
    findings = check["findings"]
    if not isinstance(findings, list):
        raise ValueError("findings must be an array")
    if metrics["findings_count"] != len(findings):
        raise ValueError("findings count does not match findings")
    for finding in findings:
        if not isinstance(finding, dict) or set(finding) != FINDING_FIELDS:
            raise ValueError("unsupported finding fields")
        for name in ("code", "path", "message"):
            if not isinstance(finding[name], str) or not finding[name]:
                raise ValueError(f"finding {name} must be a non-empty string")
        if finding["line"] is not None and (
                type(finding["line"]) is not int or finding["line"] < 1):
            raise ValueError("finding line must be a positive integer or null")
    finding_key = lambda item: (item["code"], item["path"],
                                item["line"] if item["line"] is not None else -1,
                                item["message"])
    if findings != sorted(findings, key=finding_key):
        raise ValueError("findings are not in canonical order")
    if value["status"] == "pass" and findings:
        raise ValueError("pass evidence cannot contain findings")
    if value["status"] in {"fail", "error"} and not findings:
        raise ValueError("non-pass evidence must contain findings")


def load_canonical(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("input must be a regular file of at most 1048576 bytes")
    raw = path.read_bytes()
    value = strict_json(raw.decode("utf-8"))
    validate_canonical(value)
    if raw != json_bytes(value):
        raise ValueError("input is not canonical UTF-8/LF JSON")
    return raw, value


def truncate(value, limit):
    return value[:limit], len(value) > limit


def build_packet(raw, canonical):
    check = canonical["checks"][0]
    findings = check["findings"]
    relevant = []
    truncated = len(findings) > MAX_RELEVANT_EVIDENCE
    for finding in findings[:MAX_RELEVANT_EVIDENCE]:
        code, code_cut = truncate(finding["code"], MAX_CODE_CHARS)
        path, path_cut = truncate(finding["path"], MAX_PATH_CHARS)
        message, message_cut = truncate(finding["message"], MAX_MESSAGE_CHARS)
        truncated = truncated or code_cut or path_cut or message_cut
        relevant.append({
            "code": code,
            "line": finding["line"],
            "message": message,
            "path": path,
        })

    all_paths = sorted({finding["path"] for finding in findings})
    affected_paths = []
    for path in all_paths:
        shortened, path_cut = truncate(path, MAX_PATH_CHARS)
        truncated = truncated or path_cut
        if shortened in affected_paths:
            truncated = True
        elif len(affected_paths) < MAX_AFFECTED_PATHS:
            affected_paths.append(shortened)
        else:
            truncated = True

    all_codes = sorted({finding["code"] for finding in findings})
    error_codes = []
    for code in all_codes:
        shortened, code_cut = truncate(code, MAX_CODE_CHARS)
        truncated = truncated or code_cut
        if shortened in error_codes:
            truncated = True
        elif len(error_codes) < MAX_RELEVANT_EVIDENCE:
            error_codes.append(shortened)
        else:
            truncated = True

    status = canonical["status"]
    route = "machine" if status == "fail" else "agent"
    reason = ("known-deterministic-findings" if status == "fail"
              else "unclassified-audit-error")
    return {
        "affected_paths": affected_paths,
        "artifact_hash": hashlib.sha256(raw).hexdigest(),
        "commit": canonical["subject"]["revision"],
        "dirty": canonical["subject"]["dirty"],
        "error_codes": error_codes,
        "evidence_truncated": truncated,
        "failed_check": "repository-audit",
        "relevant_evidence": relevant,
        "repeatable": None,
        "retries": 0,
        "route": route,
        "routing_reason": reason,
        "schema": "bima-agent-packet.v1",
        "stage": "repository-audit",
        "status": status,
        "total_findings": len(findings),
    }


def prepare_output(output):
    if output.is_symlink():
        raise ValueError("output directory cannot be a symlink")
    output.mkdir(parents=True, exist_ok=True)
    if not output.is_dir():
        raise ValueError("output must be a directory")
    for name in OWNED_OUTPUTS:
        path = output / name
        if path.exists() or path.is_symlink():
            path.unlink()


def generate(source_path, output):
    prepare_output(output)
    raw, canonical = load_canonical(source_path)
    if canonical["status"] == "pass":
        return "pass", None
    packet = build_packet(raw, canonical)
    packet_raw = json_bytes(packet)
    digest = hashlib.sha256(packet_raw).hexdigest()
    (output / "packet.json").write_bytes(packet_raw)
    (output / "packet.sha256").write_bytes(
        f"{digest}  packet.json\n".encode("ascii"))
    return canonical["status"], digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="canonical bima-evidence.v1 JSON")
    parser.add_argument("--output", type=Path, required=True,
                        help="trusted output directory")
    args = parser.parse_args()
    try:
        status, digest = generate(args.input, args.output)
    except (OSError, UnicodeError, ValueError, RecursionError):
        print("agent-packet: error; invalid or unreadable canonical evidence",
              file=sys.stderr)
        return 2
    if digest is None:
        print("agent-packet: not-needed; status=pass")
    else:
        route = "machine" if status == "fail" else "agent"
        print(f"agent-packet: generated; status={status}; route={route}; sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
