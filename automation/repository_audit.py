"""Offline repository hygiene checks; Python 3.11+ standard library only."""

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from urllib.parse import unquote


DEFAULT_POLICY = {"schema_version": 1, "required_files": ["README.md", "AGENTS.md"],
                  "max_file_bytes": 1048576}
MAX_POLICY_BYTES = 65536
MAX_FILES = 100000
INLINE_LINK = re.compile(r"\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+\"[^\"\n]*\")?\s*\)")


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=30).stdout


def safe_path(root, name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError("path must be a relative POSIX path")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or any(p.lower() == ".git" for p in path.parts):
        raise ValueError("path leaves repository or references Git internals")
    candidate = root
    for part in path.parts:
        candidate = candidate / part
        if candidate.is_symlink() or (hasattr(candidate, "is_junction") and candidate.is_junction()):
            raise ValueError("symlink/junction paths are not audited")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("path leaves repository")
    return candidate


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


def load_policy(root, name):
    if name is None:
        return DEFAULT_POLICY.copy(), None
    path = safe_path(root, name)
    if not path.is_file() or path.stat().st_size > MAX_POLICY_BYTES:
        raise ValueError("policy must be a regular file of at most 65536 bytes")
    raw = path.read_bytes()
    policy = strict_json(raw.decode("utf-8"))
    if not isinstance(policy, dict) or set(policy) != set(DEFAULT_POLICY):
        raise ValueError("policy must contain schema_version, required_files, max_file_bytes only")
    if type(policy["schema_version"]) is not int or policy["schema_version"] != 1:
        raise ValueError("unsupported policy schema_version")
    required = policy["required_files"]
    if not isinstance(required, list) or not required or len(required) > 100:
        raise ValueError("required_files must contain 1 to 100 paths")
    for item in required:
        safe_path(root, item)
    if len(set(required)) != len(required):
        raise ValueError("required_files must be unique")
    size = policy["max_file_bytes"]
    if type(size) is not int or not 1 <= size <= 10485760:
        raise ValueError("max_file_bytes must be an integer from 1 to 10485760")
    return policy, hashlib.sha256(raw).hexdigest()


def markdown_links(text):
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            run = marker.group(1)
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence):
                fence = None
            continue
        if fence or line.startswith(("    ", "\t")):
            continue
        line = re.sub(r"(`+).*?\1", "", line)
        for match in INLINE_LINK.finditer(line):
            yield number, match.group(1).strip("<>")


def audit(root, policy_name=None):
    root = root.resolve()
    result = {"schema_version": 1, "module": "repository-audit", "status": "error",
              "generated_at": datetime.now(timezone.utc).isoformat(),
              "validator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "python_version": sys.version.split()[0],
              "revision": None, "dirty": None, "policy_sha256": None,
              "files_checked": 0, "local_links_checked": 0, "findings": []}

    def finding(code, path, message, line=None):
        result["findings"].append({"code": code, "path": path, "line": line, "message": message})

    try:
        top = Path(os.fsdecode(git(root, "rev-parse", "--show-toplevel")).strip()).resolve()
        if top != root:
            raise ValueError("root must be the Git repository top level")
        result["revision"] = git(root, "rev-parse", "HEAD").decode("ascii").strip()
        result["dirty"] = bool(git(root, "status", "--porcelain", "--untracked-files=normal"))
        policy, result["policy_sha256"] = load_policy(root, policy_name)
        names = sorted(set(os.fsdecode(n) for n in git(
            root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split(b"\0") if n))
        if not names or len(names) > MAX_FILES:
            raise ValueError("repository inventory must contain 1 to 100000 files")
        inventory = set(names)
        for name in policy["required_files"]:
            path = safe_path(root, name)
            if name not in inventory or not path.is_file() or path.stat().st_size == 0:
                finding("required-file", name, "required file is missing, empty, or ignored")
        for name in names:
            try:
                path = safe_path(root, name)
                info = path.stat()
                if not stat.S_ISREG(info.st_mode):
                    finding("unsupported-file", name, "only regular files are supported; submodules are not traversed")
                    continue
                result["files_checked"] += 1
                if info.st_size > policy["max_file_bytes"]:
                    finding("file-size", name, f"file exceeds {policy['max_file_bytes']} bytes")
                    continue
                if path.suffix.lower() not in {".json", ".md"}:
                    continue
                content = path.read_text(encoding="utf-8")
                if path.suffix.lower() == ".json":
                    try:
                        strict_json(content)
                    except (ValueError, RecursionError):
                        finding("invalid-json", name, "invalid JSON, duplicate key, or non-finite number")
                    continue
                for line, target in markdown_links(content):
                    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith(("#", "//")):
                        continue
                    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
                    if not target:
                        continue
                    result["local_links_checked"] += 1
                    base = root if target.startswith("/") else path.parent
                    # Normalize legitimate ../ documentation links before enforcing containment.
                    absolute = Path(os.path.abspath(base / target.lstrip("/")))
                    if not absolute.is_relative_to(root):
                        finding("unsafe-link", name, "local link leaves repository", line)
                        continue
                    try:
                        linked = safe_path(root, absolute.relative_to(root).as_posix())
                    except ValueError:
                        finding("unsafe-link", name, "local link references an unsafe path", line)
                        continue
                    relative = linked.relative_to(root).as_posix()
                    present = relative in inventory or any(n.startswith(relative.rstrip("/") + "/") for n in names)
                    if not linked.exists() or (relative != "." and not present):
                        finding("broken-link", name, "local link target is absent from repository inventory", line)
            except (OSError, ValueError, UnicodeError):
                finding("unreadable-file", name, "file is missing, unsafe, or not UTF-8 text")
        result["status"] = "fail" if result["findings"] else "pass"
    except (OSError, ValueError, RecursionError, subprocess.SubprocessError):
        finding("audit-error", policy_name or ".", "cannot audit repository or policy; check Git root, HEAD, paths, and policy contract")
    return result


def write_report(result, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    lines = ["# Repository audit", "", f"Status: **{result['status']}**", "",
             f"Revision: `{result['revision']}`; dirty: `{result['dirty']}`", "",
             f"Files checked: {result['files_checked']}; local links checked: {result['local_links_checked']}", "",
             "Scope: required files, file sizes, JSON syntax, and supported inline local Markdown links.",
             "This is not a secrets scan, workflow security audit, or application test.", ""]
    for item in result["findings"]:
        value = json.dumps(item, ensure_ascii=True)
        lines.append("<pre>" + html.escape(value) + "</pre>")
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--policy", help="repository-relative JSON policy; omission uses built-in defaults")
    parser.add_argument("--output", type=Path, required=True, help="trusted output directory outside audited inputs")
    args = parser.parse_args()
    result = audit(args.root, args.policy)
    write_report(result, args.output)
    print(f"repository-audit: {result['status']}; files={result['files_checked']}; findings={len(result['findings'])}")
    return {"pass": 0, "fail": 1, "error": 2}[result["status"]]


if __name__ == "__main__":
    sys.exit(main())
