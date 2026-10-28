"""Validate the reusable workflow catalog against the workflows it lists."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = "catalog/workflows.json"
ID = re.compile(r"^[a-z][a-z0-9-]{1,39}$")
PATH = re.compile(r"^\.github/workflows/[a-z0-9-]+\.yml$")
DOCS = re.compile(r"^docs/standards/[A-Z0-9-]+\.md$")
CONSUMER = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
STATUSES = {"experimental", "beta", "stable"}
ENTRY_KEYS = {"id", "path", "status", "docs", "consumers", "sha256", "summary"}
TOP_KEYS = {"schema", "schema_version", "workflows"}
LIMITS = {"workflows": 50, "consumers": 20, "summary": 200}


class CatalogError(RuntimeError):
    """The catalog does not match the repository it describes."""


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"non-finite number: {value}")


def load_json(path):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CatalogError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text, object_pairs_hook=reject_duplicates,
                          parse_constant=reject_constant)
    except ValueError as exc:
        raise CatalogError(f"invalid JSON in {path}: {exc}") from exc


def regular_file(root, relative, label):
    if not isinstance(relative, str) or not relative:
        raise CatalogError(f"{label} must be a non-empty string")
    candidate = root / relative
    try:
        resolved = candidate.resolve()
    except OSError as exc:
        raise CatalogError(f"{label} cannot be resolved: {exc}") from exc
    if root.resolve() not in resolved.parents or not resolved.is_file():
        raise CatalogError(f"{label} must be a regular file inside the repository: {relative}")
    return resolved


def check_entry(root, entry, seen):
    if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
        raise CatalogError(f"entry keys must be exactly {sorted(ENTRY_KEYS)}")
    identifier = entry["id"]
    if not isinstance(identifier, str) or not ID.fullmatch(identifier):
        raise CatalogError(f"invalid workflow id: {identifier!r}")
    if identifier in seen:
        raise CatalogError(f"duplicate workflow id: {identifier}")
    seen.add(identifier)

    path = entry["path"]
    if not isinstance(path, str) or not PATH.fullmatch(path):
        raise CatalogError(f"{identifier}: path must be .github/workflows/<name>.yml")
    workflow = regular_file(root, path, f"{identifier}.path")
    if "workflow_call:" not in workflow.read_text(encoding="utf-8"):
        raise CatalogError(f"{identifier}: workflow does not declare workflow_call")

    if entry["status"] not in STATUSES:
        raise CatalogError(f"{identifier}: status must be one of {sorted(STATUSES)}")

    docs = entry["docs"]
    if not isinstance(docs, str) or not DOCS.fullmatch(docs):
        raise CatalogError(f"{identifier}: docs must be docs/standards/<NAME>.md")
    regular_file(root, docs, f"{identifier}.docs")

    consumers = entry["consumers"]
    if not isinstance(consumers, list) or len(consumers) > LIMITS["consumers"]:
        raise CatalogError(f"{identifier}: consumers must be a list of at most 20")
    for consumer in consumers:
        if not isinstance(consumer, str) or not CONSUMER.fullmatch(consumer):
            raise CatalogError(f"{identifier}: invalid consumer: {consumer!r}")
    if len(set(consumers)) != len(consumers):
        raise CatalogError(f"{identifier}: duplicate consumer")

    digest = entry["sha256"]
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise CatalogError(f"{identifier}: sha256 must be 64 lowercase hex characters")
    actual = hashlib.sha256(workflow.read_bytes()).hexdigest()
    if actual != digest:
        raise CatalogError(f"{identifier}: sha256 does not match {path}")

    summary = entry["summary"]
    if (not isinstance(summary, str) or not 1 <= len(summary) <= LIMITS["summary"]
            or any(ord(character) < 32 for character in summary)):
        raise CatalogError(f"{identifier}: summary must be 1-200 printable characters")


def validate(root, catalog_path):
    document = load_json(catalog_path)
    if not isinstance(document, dict) or set(document) != TOP_KEYS:
        raise CatalogError(f"catalog keys must be exactly {sorted(TOP_KEYS)}")
    if document["schema"] != "bima-workflow-catalog.v1":
        raise CatalogError("schema must be bima-workflow-catalog.v1")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise CatalogError("schema_version must be the integer 1")
    workflows = document["workflows"]
    if not isinstance(workflows, list) or not 1 <= len(workflows) <= LIMITS["workflows"]:
        raise CatalogError("workflows must contain 1-50 entries")
    seen = set()
    for entry in workflows:
        check_entry(root, entry, seen)
    return len(workflows)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate catalog/workflows.json against the real workflows.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    arguments = parser.parse_args(argv)
    try:
        root = arguments.root.resolve()
        catalog = regular_file(root, arguments.catalog, "catalog")
        count = validate(root, catalog)
    except (CatalogError, OSError) as exc:
        print(f"workflow-catalog: fail: {exc}", file=sys.stderr)
        return 2
    print(f"workflow-catalog: pass; workflows={count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
