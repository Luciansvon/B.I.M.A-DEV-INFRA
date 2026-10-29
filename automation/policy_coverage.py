"""Assert the audit policy protects every durable implementation surface."""

import argparse
import json
import sys
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ".bima/audit.json"
DEFAULT_CATALOG = "catalog/workflows.json"
FIXED = ("docs/NEXT.md",)
GLOBS = ("automation/*.py", "automation/*.sh", "schemas/*.schema.json",
         ".github/workflows/*.yml", "docs/standards/*.md", "docs/architecture/*.md",
         "docs/decisions/*.md", "docs/incidents/*.md")
MAX_REQUIRED = 160


class CoverageError(RuntimeError):
    """A durable surface is not protected by required_files."""


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"non-finite number: {value}")


def load_json(path, label):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CoverageError(f"cannot read {label}: {exc}") from exc
    try:
        return json.loads(text, object_pairs_hook=reject_duplicates,
                          parse_constant=reject_constant)
    except ValueError as exc:
        raise CoverageError(f"invalid JSON in {label}: {exc}") from exc


def required_files(document):
    items = document.get("required_files") if isinstance(document, dict) else None
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_REQUIRED:
        raise CoverageError(f"required_files must be a list of 1 to {MAX_REQUIRED} paths")
    seen = set()
    for item in items:
        if not isinstance(item, str) or not item:
            raise CoverageError("required_files entries must be non-empty strings")
        path = PurePosixPath(item)
        if "\\" in item or ":" in item or path.is_absolute() or ".." in path.parts:
            raise CoverageError(f"required_files entry must stay inside the repository: {item}")
        if item in seen:
            raise CoverageError(f"duplicate required entry: {item}")
        seen.add(item)
    return seen


def catalog_surfaces(root, catalog):
    entries = load_json(catalog, DEFAULT_CATALOG)
    entries = entries.get("workflows") if isinstance(entries, dict) else None
    if not isinstance(entries, list):
        raise CoverageError("catalog workflows must be a list")
    surfaces = set()
    for entry in entries:
        for key in ("path", "docs"):
            value = entry.get(key) if isinstance(entry, dict) else None
            if not isinstance(value, str) or not value:
                raise CoverageError(f"catalog entry is missing {key}")
            surfaces.add(value)
    return surfaces


def surfaces(root):
    found = set(FIXED)
    for pattern in GLOBS:
        for path in root.glob(pattern):
            if path.is_file():
                found.add(path.relative_to(root).as_posix())
    return found


def validate(root):
    root = root.resolve()
    required = required_files(load_json(root / DEFAULT_POLICY, DEFAULT_POLICY))
    expected = surfaces(root) | catalog_surfaces(root, root / DEFAULT_CATALOG)
    covered = expected & required
    uncovered = sorted(expected - covered)
    if uncovered:
        raise CoverageError(f"not protected by required_files: {', '.join(uncovered[:5])}")
    for name in sorted(required):
        if not (root / name).is_file():
            raise CoverageError(f"required file is missing: {name}")
    return len(required), len(covered)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Assert .bima/audit.json required_files covers every durable surface.")
    parser.add_argument("--root", type=Path, default=ROOT)
    arguments = parser.parse_args(argv)
    try:
        required, covered = validate(arguments.root)
    except (CoverageError, OSError) as exc:
        print(f"policy-coverage: fail: {exc}", file=sys.stderr)
        return 2
    print(f"policy-coverage: pass; required={required}; covered={covered}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
