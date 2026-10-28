"""Create a project scaffold from templates/project with one pinned infrastructure ref."""

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "project"
SHA = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDER = re.compile(r"__[A-Z][A-Z0-9_]*__")
PLACEHOLDERS = {"__INFRA_REF__", "__PROJECT_NAME__"}


class BootstrapError(RuntimeError):
    """The scaffold cannot be created without weakening a contract."""


def canonical(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def read_template():
    files = []
    for path in sorted(TEMPLATE.rglob("*")):
        if path.is_symlink():
            raise BootstrapError(
                f"template contains a symlink: {path.relative_to(TEMPLATE).as_posix()}")
        if not path.is_file():
            continue
        relative = path.relative_to(TEMPLATE).as_posix()
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BootstrapError(f"template file is not UTF-8: {relative}") from exc
        unknown = set(PLACEHOLDER.findall(text)) - PLACEHOLDERS
        if unknown:
            raise BootstrapError(
                f"unknown placeholder in {relative}: {sorted(unknown)}")
        files.append((relative, text))
    if not files:
        raise BootstrapError("template directory is empty")
    return files


def render(files, project_name, infra_ref):
    rendered = []
    for relative, text in files:
        output = (text.replace("__PROJECT_NAME__", project_name)
                      .replace("__INFRA_REF__", infra_ref))
        leftover = PLACEHOLDER.findall(output)
        if leftover:
            raise BootstrapError(f"unresolved placeholder in {relative}: {leftover}")
        data = output.encode("utf-8")
        rendered.append((relative, data))
    return rendered


def resolve_target(target):
    resolved = target.resolve()
    template = TEMPLATE.resolve()
    if resolved == template or template in resolved.parents:
        raise BootstrapError("target must not be inside the template directory")
    if resolved.exists():
        if not resolved.is_dir():
            raise BootstrapError(f"target is not a directory: {resolved}")
        if any(resolved.iterdir()):
            raise BootstrapError(f"target is not empty: {resolved}")
        return resolved, False
    return resolved, True


def validate_name(project_name):
    name = project_name.strip()
    if not 1 <= len(name) <= 100:
        raise BootstrapError("project name must be 1-100 characters")
    if "__" in name or any(ord(character) < 32 or ord(character) == 127
                           for character in name):
        raise BootstrapError("project name must not contain control characters or '__'")
    return name


def create(target, created, rendered):
    written = []
    try:
        target.mkdir(parents=True, exist_ok=True)
        for relative, data in rendered:
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                raise BootstrapError(f"target already contains {relative}")
            destination.write_bytes(data)
            written.append(destination)
    except Exception:
        if created:
            shutil.rmtree(target, ignore_errors=True)
        else:
            for path in reversed(written):
                path.unlink(missing_ok=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Create a project scaffold with one pinned DEV-INFRA commit.")
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--infra-ref", required=True)
    parser.add_argument("--project-name", required=True)
    arguments = parser.parse_args(argv)

    try:
        if not SHA.fullmatch(arguments.infra_ref):
            raise BootstrapError("infra-ref must be a full lowercase commit SHA")
        project_name = validate_name(arguments.project_name)
        rendered = render(read_template(), project_name, arguments.infra_ref)
        target, created = resolve_target(arguments.target)
        create(target, created, rendered)
    except (BootstrapError, OSError) as exc:
        print(f"bootstrap-project: error: {exc}", file=sys.stderr)
        return 2

    manifest = {
        "schema_version": 1,
        "project_name": project_name,
        "infra_ref": arguments.infra_ref,
        "files": [
            {
                "path": relative,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for relative, data in rendered
        ],
    }
    sys.stdout.buffer.write(canonical(manifest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
