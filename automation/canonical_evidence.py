"""Normalize repository-audit output into hashable B.I.M.A evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import sys


MAX_INPUT_BYTES = 1048576
OWNED_OUTPUTS = ("canonical.json", "execution.json", "canonical.sha256")
SOURCE_FIELDS = {
    "schema_version", "module", "status", "generated_at", "validator_sha256",
    "python_version", "revision", "dirty", "policy_sha256", "files_checked",
    "local_links_checked", "findings",
}
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


def nonnegative_integer(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def validate_source(source):
    if not isinstance(source, dict) or set(source) != SOURCE_FIELDS:
        raise ValueError("unsupported repository-audit result fields")
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("unsupported repository-audit schema")
    if source["module"] != "repository-audit":
        raise ValueError("unsupported evidence module")
    if source["status"] not in {"pass", "fail", "error"}:
        raise ValueError("unsupported status")
    if not isinstance(source["generated_at"], str) or not source["generated_at"]:
        raise ValueError("generated_at must be a non-empty string")
    if not isinstance(source["python_version"], str) or not source["python_version"]:
        raise ValueError("python_version must be a non-empty string")
    if not isinstance(source["validator_sha256"], str) or not SHA256.fullmatch(source["validator_sha256"]):
        raise ValueError("invalid validator SHA-256")
    if source["policy_sha256"] is not None and (
            not isinstance(source["policy_sha256"], str)
            or not SHA256.fullmatch(source["policy_sha256"])):
        raise ValueError("invalid policy SHA-256")
    if source["revision"] is not None and (
            not isinstance(source["revision"], str) or not REVISION.fullmatch(source["revision"])):
        raise ValueError("invalid revision")
    if source["dirty"] is not None and type(source["dirty"]) is not bool:
        raise ValueError("dirty must be boolean or null")
    nonnegative_integer(source["files_checked"], "files_checked")
    nonnegative_integer(source["local_links_checked"], "local_links_checked")
    if not isinstance(source["findings"], list):
        raise ValueError("findings must be an array")
    for finding in source["findings"]:
        if not isinstance(finding, dict) or set(finding) != FINDING_FIELDS:
            raise ValueError("unsupported finding fields")
        for key in ("code", "path", "message"):
            if not isinstance(finding[key], str) or not finding[key]:
                raise ValueError(f"finding {key} must be a non-empty string")
        if finding["line"] is not None and (
                type(finding["line"]) is not int or finding["line"] < 1):
            raise ValueError("finding line must be a positive integer or null")
    if source["status"] == "pass" and source["findings"]:
        raise ValueError("pass result cannot contain findings")
    if source["status"] in {"fail", "error"} and not source["findings"]:
        raise ValueError("non-pass result must contain findings")
    if source["status"] in {"pass", "fail"} and (
            source["revision"] is None or source["dirty"] is None):
        raise ValueError("completed audit requires revision and dirty state")


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2,
                       sort_keys=True) + "\n").encode("utf-8")


def finding_key(finding):
    return (finding["code"], finding["path"],
            finding["line"] if finding["line"] is not None else -1,
            finding["message"])


def canonicalize(source):
    validate_source(source)
    findings = [dict(item) for item in sorted(source["findings"], key=finding_key)]
    script_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "checks": [{
            "findings": findings,
            "id": "repository-audit",
            "metrics": {
                "files_checked": source["files_checked"],
                "findings_count": len(findings),
                "local_links_checked": source["local_links_checked"],
            },
            "status": source["status"],
        }],
        "policy": {"sha256": source["policy_sha256"]},
        "schema": "bima-evidence.v1",
        "status": source["status"],
        "subject": {
            "dirty": source["dirty"],
            "revision": source["revision"],
        },
        "toolchain": [
            {"name": "canonical-evidence", "sha256": script_sha256},
            {"name": "python", "version": source["python_version"]},
            {"name": "repository-audit", "sha256": source["validator_sha256"]},
        ],
    }


def load_source(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("input must be a regular file of at most 1048576 bytes")
    raw = path.read_bytes()
    source = strict_json(raw.decode("utf-8"))
    validate_source(source)
    return raw, source


def generate(source_path, output):
    if output.is_symlink():
        raise ValueError("output directory cannot be a symlink")
    output.mkdir(parents=True, exist_ok=True)
    if not output.is_dir():
        raise ValueError("output must be a directory")
    for name in OWNED_OUTPUTS:
        path = output / name
        if path.exists() or path.is_symlink():
            path.unlink()
    raw, source = load_source(source_path)
    canonical = canonicalize(source)
    canonical_raw = json_bytes(canonical)
    canonical_sha256 = hashlib.sha256(canonical_raw).hexdigest()
    execution = {
        "canonical": {"name": "canonical.json", "sha256": canonical_sha256},
        "runtime": {
            "machine": platform.machine() or "unknown",
            "python_version": platform.python_version(),
            "system": platform.system() or "unknown",
        },
        "schema": "bima-evidence.execution.v1",
        "source": {
            "generated_at": source["generated_at"],
            "name": source_path.name,
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
    }
    (output / "canonical.json").write_bytes(canonical_raw)
    (output / "execution.json").write_bytes(json_bytes(execution))
    (output / "canonical.sha256").write_bytes(
        f"{canonical_sha256}  canonical.json\n".encode("ascii"))
    return canonical_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="repository-audit result.json")
    parser.add_argument("--output", type=Path, required=True,
                        help="trusted output directory")
    args = parser.parse_args()
    try:
        digest = generate(args.input, args.output)
    except (OSError, UnicodeError, ValueError, RecursionError):
        print("canonical-evidence: error; invalid or unreadable repository-audit result",
              file=sys.stderr)
        return 2
    print(f"canonical-evidence: pass; sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
