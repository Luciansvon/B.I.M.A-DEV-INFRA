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
CALL = "workflow_call:"
SECTION = re.compile(r"^    (inputs|outputs):\s*$")
DECLARED = re.compile(r"^      ([A-Za-z0-9_.-]+):\s*$")
HEADING = re.compile(r"^##\s+(.+?)\s*$")
REQUIRED_SECTIONS = (
    "Identity", "Triggers", "Inputs", "Outputs", "Runner", "Permissions",
    "Execution limits", "Evidence", "Failure contract", "Security",
    "Compatibility",
)


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


def declared_io(text):
    """Names at the fixed indentation of a workflow_call inputs/outputs block."""
    declared = {"inputs": set(), "outputs": set()}
    section = None
    inside = False
    for line in text.splitlines():
        if line.rstrip() == "  " + CALL:
            inside, section = True, None
            continue
        if not inside:
            continue
        if line and not line.startswith(" "):
            break
        if line.startswith("  ") and not line.startswith("    "):
            if line.strip():
                break
            continue
        match = SECTION.match(line)
        if match:
            section = match.group(1)
            continue
        match = DECLARED.match(line)
        if match and section:
            declared[section].add(match.group(1))
    return declared["inputs"], declared["outputs"]


def validation_text(root):
    directory = root / "docs" / "audits"
    if not directory.is_dir():
        return ""
    parts = []
    for path in sorted(directory.glob("VALIDATION-*.md")):
        try:
            parts.append(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            raise CatalogError(f"cannot read {path}: {exc}") from exc
    return "\n".join(parts)


def documented_sections(text):
    sections = {}
    current = None
    for line in text.splitlines():
        heading = HEADING.match(line)
        if heading:
            current = heading.group(1).casefold()
            sections[current] = False
            continue
        if current is not None and line.strip():
            sections[current] = True
    return sections


def check_sections(identifier, documentation):
    sections = documented_sections(documentation)
    missing = [
        label for label in REQUIRED_SECTIONS
        if not any(label.casefold() in heading and content
                   for heading, content in sections.items())
    ]
    if missing:
        raise CatalogError(
            f"{identifier}: docs must document sections: {', '.join(missing)}")


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
    text = workflow.read_text(encoding="utf-8")
    if CALL not in text:
        raise CatalogError(f"{identifier}: workflow does not declare workflow_call")

    if entry["status"] not in STATUSES:
        raise CatalogError(f"{identifier}: status must be one of {sorted(STATUSES)}")

    docs = entry["docs"]
    if not isinstance(docs, str) or not DOCS.fullmatch(docs):
        raise CatalogError(f"{identifier}: docs must be docs/standards/<NAME>.md")
    documentation_path = regular_file(root, docs, f"{identifier}.docs")
    try:
        documentation = documentation_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CatalogError(f"{identifier}: cannot read docs: {exc}") from exc
    inputs, outputs = declared_io(text)
    for kind, names in (("input", inputs), ("output", outputs)):
        for name in sorted(names):
            if f"`{name}`" not in documentation:
                raise CatalogError(f"{identifier}: docs must name {kind} `{name}`")
    check_sections(identifier, documentation)

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
    check_inventory(root, [entry["path"] for entry in workflows])
    evidence = None
    for entry in workflows:
        consumers = entry["consumers"]
        if entry["status"] in {"beta", "stable"} and not consumers:
            raise CatalogError(
                f"{entry['id']}: {entry['status']} requires at least one consumer")
        if consumers and evidence is None:
            evidence = validation_text(root)
        for consumer in consumers:
            if consumer not in evidence:
                raise CatalogError(
                    f"{entry['id']}: consumer has no validation evidence: {consumer}")
    return len(workflows)


def check_inventory(root, paths):
    counts = {}
    for path in paths:
        counts[path] = counts.get(path, 0) + 1
    directory = root / ".github" / "workflows"
    if not directory.is_dir():
        raise CatalogError(".github/workflows must be a directory")
    for candidate in sorted(directory.glob("*.yml")):
        relative = f".github/workflows/{candidate.name}"
        try:
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise CatalogError(f"cannot read {relative}: {exc}") from exc
        if CALL not in text:
            continue
        count = counts.get(relative, 0)
        if count == 0:
            raise CatalogError(f"reusable workflow is not in the catalog: {relative}")
        if count > 1:
            raise CatalogError(f"reusable workflow is listed more than once: {relative}")


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
