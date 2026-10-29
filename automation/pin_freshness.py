"""Compare local reusable-workflow pins with the reviewed catalog hashes."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = "catalog/workflows.json"
REF = re.compile(
    r"Luciansvon/B\.I\.M\.A-DEV-INFRA/(\.github/workflows/[a-z0-9-]+\.yml)@"
    r"([0-9a-f]{40})")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

class FreshnessError(RuntimeError):
    """A caller pin does not match the reviewed workflow bytes."""


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=30).stdout


def catalog_entries(root, catalog_path):
    document = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = {}
    for entry in document.get("workflows", []):
        path, digest = entry.get("path"), entry.get("sha256")
        if not isinstance(path, str) or not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise FreshnessError("catalog entry has an invalid path or sha256")
        entries[path] = digest
    return entries


def references(root):
    files = sorted((root / ".github" / "workflows").glob("*.yml"))
    template = root / "templates"
    if template.is_dir():
        files.extend(sorted(template.rglob("*.yml")))
    for path in files:
        for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            for match in REF.finditer(line):
                yield path, number, match.group(1), match.group(2)


def validate(root, catalog_path, consumer_root=None):
    entries = catalog_entries(root, catalog_path)
    source = (consumer_root or root).resolve()
    shallow = git(root, "rev-parse", "--is-shallow-repository").strip() == b"true"
    checked = 0
    for path, number, workflow_path, revision in references(source):
        label = f"{path.relative_to(source).as_posix()}:{number}"
        if workflow_path not in entries:
            raise FreshnessError(f"{label}: workflow is not in the catalog: {workflow_path}")
        try:
            blob = git(root, "show", f"{revision}:{workflow_path}")
        except subprocess.SubprocessError as exc:
            state = "UNVERIFIED" if shallow else "unknown revision or path"
            raise FreshnessError(f"{label}: {state} {revision}") from exc
        actual = hashlib.sha256(blob).hexdigest()
        if actual != entries[workflow_path]:
            raise FreshnessError(
                f"{label}: pinned bytes differ from the reviewed catalog for {workflow_path}")
        checked += 1
    return checked, len(entries)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compare reusable-workflow pins with the reviewed catalog.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument(
        "--consumer-root", type=Path,
        help="consumer checkout whose pins are compared with the catalog in --root")
    arguments = parser.parse_args(argv)
    try:
        root = arguments.root.resolve()
        if arguments.consumer_root is not None and not arguments.consumer_root.is_dir():
            raise FreshnessError(
                f"consumer root is not a directory: {arguments.consumer_root}")
        checked, total = validate(
            root, root / arguments.catalog, arguments.consumer_root)
    except (FreshnessError, OSError, ValueError, KeyError,
            json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"pin-freshness: fail: {exc}", file=sys.stderr)
        return 2
    print(f"pin-freshness: pass; refs={checked}; catalog={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
