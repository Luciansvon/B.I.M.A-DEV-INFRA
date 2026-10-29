"""Verify self-repository reusable-workflow references point at real revisions."""

import argparse
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "Luciansvon/B.I.M.A-DEV-INFRA"
LOCAL_PREFIX = "./.github/workflows/"
EXTERNAL = re.compile(
    r"^" + re.escape(REPOSITORY)
    + r"/\.github/workflows/([^@\s]+)@([^@\s]+)$")
WORKFLOW_NAME = re.compile(r"^[a-z0-9-]+\.yml$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
USES = re.compile(r"^(?P<indent> *)(?P<dash>- +)?uses: *(?P<value>.*)$")
WITH = re.compile(r"^ *with: *$")
INPUT = re.compile(r"^ +infra-ref: *(?P<value>.*)$")
PLACEHOLDER = "__INFRA_REF__"
TEMPLATES = "templates/"


class WorkflowRefError(RuntimeError):
    """A reusable-workflow reference is not verifiable."""


def _scalar(value):
    value = value.split(" #", 1)[0].strip()
    if len(value) > 1 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def _infra_ref(lines, index, indent):
    """Return the infra-ref input of the with block that belongs to a uses line."""
    inside = False
    for line in lines[index + 1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        current = len(line) - len(line.lstrip(" "))
        if current < indent or (current == indent and (inside or not WITH.match(line))):
            return None
        if current == indent:
            inside = True
            continue
        match = INPUT.match(line)
        if match:
            return _scalar(match["value"])
    return None


def _references(text):
    """Yield (line number, uses value, infra-ref of the same block)."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = USES.match(line)
        if match:
            indent = len(match["indent"]) + (2 if match["dash"] else 0)
            yield index + 1, _scalar(match["value"]), _infra_ref(lines, index, indent)


def _is_workflow_ref(value):
    return value.startswith(LOCAL_PREFIX) or EXTERNAL.match(value) is not None


def _git(root, *args):
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args], check=False, capture_output=True,
            timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise WorkflowRefError("cannot inspect repository history") from exc


def _is_shallow(root):
    run = _git(root, "rev-parse", "--is-shallow-repository")
    if run.returncode != 0:
        raise WorkflowRefError("cannot inspect repository history")
    return run.stdout.decode("ascii", "replace").strip() == "true"


def _verify_reference(root, relative, line, value, infra_ref):
    if value.startswith(LOCAL_PREFIX):
        workflows = (root / ".github" / "workflows").resolve()
        candidate = root / ".github" / "workflows" / value[len(LOCAL_PREFIX):]
        if not candidate.resolve().is_relative_to(workflows) or not candidate.is_file():
            raise WorkflowRefError(
                f"{relative}:{line}: local workflow does not exist: {value}")
        return

    match = EXTERNAL.match(value)
    if match is None:
        return  # third-party action pins are owned by pinact and zizmor
    name, ref = match.groups()
    if not WORKFLOW_NAME.fullmatch(name):
        raise WorkflowRefError(
            f"{relative}:{line}: workflow path must be .github/workflows/<name>.yml")
    if ref == PLACEHOLDER and relative.startswith(TEMPLATES):
        # shortcut: the template ships an unrendered placeholder; bootstrap writes a full SHA.
        if infra_ref not in (None, PLACEHOLDER):
            raise WorkflowRefError(
                f"{relative}:{line}: infra-ref does not match the workflow ref")
        return
    if not REVISION.fullmatch(ref):
        raise WorkflowRefError(
            f"{relative}:{line}: reusable workflow ref is not a full commit SHA")
    if infra_ref is not None and infra_ref != ref:
        raise WorkflowRefError(
            f"{relative}:{line}: infra-ref does not match the workflow ref")
    if _git(root, "cat-file", "-e", f"{ref}^{{commit}}").returncode != 0:
        raise WorkflowRefError(
            f"{relative}:{line}: revision {ref} is not available")
    if _git(root, "cat-file", "-e", f"{ref}:.github/workflows/{name}").returncode != 0:
        raise WorkflowRefError(
            f"{relative}:{line}: workflow is missing at revision {ref}")


def verify(root):
    root = Path(root).resolve()
    files = 0
    refs = 0
    sources = sorted((root / ".github" / "workflows").glob("*.yml"))
    sources += sorted((root / "templates").rglob("*.yml"))
    for path in sources:
        files += 1
        relative = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise WorkflowRefError(f"{relative}:1: cannot be read: {exc}") from exc
        for line, value, infra_ref in _references(text):
            if _is_workflow_ref(value):
                refs += 1
                _verify_reference(root, relative, line, value, infra_ref)
    return files, refs


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify reusable-workflow references against real revisions.")
    parser.add_argument("--root", type=Path, default=ROOT)
    arguments = parser.parse_args(argv)
    try:
        root = arguments.root.resolve()
        if _is_shallow(root):
            print("workflow-refs: UNVERIFIED: shallow checkout cannot prove revisions",
                  file=sys.stderr)
            return 2
        files, refs = verify(root)
    except (WorkflowRefError, OSError) as exc:
        print(f"workflow-refs: fail: {exc}", file=sys.stderr)
        return 2
    print(f"workflow-refs: pass; files={files}; refs={refs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
