"""Validate the docs/NEXT.md state board and surface candidate work."""

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROADMAP = "docs/NEXT.md"
DEFAULT_TASKFILE = "Taskfile.yml"
DEFAULT_POLICY = ".bima/audit.json"
ID = re.compile(r"^[A-Z][A-Z0-9]*-[0-9]{2}$")
GATE = re.compile(r"^(consumer|hosted-run|corpus|owner|provider):\s*\S.+$")
VERIFY_TASK = re.compile(r"^task ([a-z0-9][a-z0-9-]*)$")
VERIFY_SCRIPT = re.compile(r"^automation/[a-z0-9_]+\.py$")
SEPARATOR = re.compile(r"^:?-{3,}:?$")
STATES = {"actionable", "active", "blocked", "done"}
COLUMNS = ["id", "why", "state", "gate", "precursor", "verify", "evidence",
           "done when", "review-by"]
MAX_REVIEW_DAYS = 90
LANE_STATES = {"actionable": {"actionable", "active"},
               "gated": {"blocked"},
               "done": {"done"}}
COVERAGE_DIRS = ("automation", "schemas", ".github/workflows",
                 "docs/standards", "docs/architecture")


class RoadmapError(RuntimeError):
    """The roadmap does not satisfy its own work-availability contract."""


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RoadmapError(f"cannot read {path}: {exc}") from exc


def lane_for(heading):
    if heading.startswith("## Lane 1"):
        return "actionable"
    if heading.startswith("## Lane 2"):
        return "gated"
    if heading.startswith("## Done"):
        return "done"
    return None


def parse_rows(text):
    lane = None
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            lane = lane_for(line)
            continue
        stripped = line.strip()
        if lane is None or not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and cells[0] in {"id", COLUMNS[0]}:
            continue
        if cells and all(SEPARATOR.fullmatch(cell) for cell in cells if cell):
            continue
        yield lane, number, cells


def task_names(taskfile):
    return set(re.findall(r"^  ([a-z0-9][a-z0-9-]*):\s*$",
                          read_text(taskfile), re.MULTILINE))


def parse_date(value, label):
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise RoadmapError(f"{label}: review-by must be YYYY-MM-DD") from exc


def check_verify(root, task_set, value, label):
    task = VERIFY_TASK.fullmatch(value)
    if task:
        if task.group(1) not in task_set:
            raise RoadmapError(f"{label}: unknown Taskfile task: {task.group(1)}")
        return
    if VERIFY_SCRIPT.fullmatch(value):
        if not (root / value).is_file():
            raise RoadmapError(f"{label}: verify script is missing: {value}")
        return
    raise RoadmapError(f"{label}: verify must be 'task <name>' or automation/<name>.py")


def check_evidence(root, value, identifier, label):
    if value in {"-", "—"}:
        raise RoadmapError(f"{label}: done item needs committed evidence")
    candidate = (root / value).resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        raise RoadmapError(f"{label}: evidence path is missing: {value}")
    if identifier not in read_text(candidate):
        raise RoadmapError(
            f"{label}: evidence does not mention {identifier}: {value}")


def validate(root, roadmap, taskfile, today):
    text = read_text(roadmap)
    task_set = task_names(taskfile)
    rows = list(parse_rows(text))
    if not rows:
        raise RoadmapError("Lane 1 is empty; add locally completable work before merging")
    limit = today + dt.timedelta(days=MAX_REVIEW_DAYS)
    seen = {}
    counts = {"actionable": 0, "gated": 0, "done": 0}
    for lane, number, cells in rows:
        if len(cells) != len(COLUMNS):
            raise RoadmapError(f"line {number}: expected {len(COLUMNS)} columns, got {len(cells)}")
        record = dict(zip(COLUMNS, cells))
        identifier = record["id"]
        label = f"line {number} ({identifier})"
        if not ID.fullmatch(identifier):
            raise RoadmapError(f"{label}: id must look like P4-01")
        if identifier in seen:
            raise RoadmapError(f"{label}: duplicate id")
        if record["state"] not in STATES:
            raise RoadmapError(f"{label}: state must be one of {sorted(STATES)}")
        if record["state"] not in LANE_STATES[lane]:
            raise RoadmapError(f"{label}: state '{record['state']}' is not valid in this lane")
        if not record["why"] or len(record["why"]) > 200:
            raise RoadmapError(f"{label}: why must be 1-200 characters")
        if not record["done when"]:
            raise RoadmapError(f"{label}: done when is required")
        counts[lane] += 1
        seen[identifier] = record

    for identifier, record in seen.items():
        label = f"{identifier}"
        check_verify(root, task_set, record["verify"], label)
        if record["state"] == "blocked":
            if not GATE.fullmatch(record["gate"]):
                raise RoadmapError(
                    f"{label}: blocked item needs a concrete gate "
                    "(consumer|hosted-run|corpus|owner|provider): <artifact>")
            precursor = record["precursor"]
            if precursor in {"-", "—"} or precursor not in seen:
                raise RoadmapError(f"{label}: blocked item needs an existing precursor id")
            if seen[precursor]["state"] not in {"actionable", "active", "done"}:
                raise RoadmapError(f"{label}: precursor {precursor} is itself blocked")
        else:
            if record["gate"] not in {"-", "—"}:
                raise RoadmapError(f"{label}: only blocked items may carry a gate")
            if record["precursor"] not in {"-", "—"}:
                raise RoadmapError(f"{label}: only blocked items may carry a precursor")
        if record["state"] == "done":
            check_evidence(root, record["evidence"], identifier, label)
            continue
        if record["evidence"] not in {"-", "—"}:
            raise RoadmapError(f"{label}: unfinished item must not claim evidence")
        review = parse_date(record["review-by"], label)
        if review < today:
            raise RoadmapError(f"{label}: review-by has expired ({review})")
        if review > limit:
            raise RoadmapError(f"{label}: review-by must be within {MAX_REVIEW_DAYS} days")

    if counts["actionable"] == 0:
        raise RoadmapError(
            "Lane 1 is empty; add locally completable work before merging")
    return counts


def collect_candidates(root, policy_path):
    findings = []
    try:
        policy = json.loads(read_text(policy_path))
    except (RoadmapError, ValueError):
        return [("policy", "cannot read required_files policy")]
    required = set(policy.get("required_files", []))
    for directory in COVERAGE_DIRS:
        base = root / directory
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if directory == "automation" and path.suffix not in {".py", ".sh"}:
                continue
            if directory == "schemas" and not path.name.endswith(".schema.json"):
                continue
            if directory == ".github/workflows" and path.suffix != ".yml":
                continue
            if directory.startswith("docs/") and path.suffix != ".md":
                continue
            relative = path.relative_to(root).as_posix()
            if relative not in required:
                findings.append(("required-file", relative))
    tests = root / "tests"
    test_names = {path.name for path in tests.glob("test_*.py")} if tests.is_dir() else set()
    test_text = "\n".join(read_text(path) for path in sorted(tests.glob("test_*.py"))) \
        if tests.is_dir() else ""
    for path in sorted((root / "automation").glob("*")):
        if path.suffix not in {".py", ".sh"} or path.name == "__init__.py":
            continue
        stem = path.stem
        if path.suffix == ".py" and f"test_{stem}.py" not in test_names \
                and stem not in test_text:
            findings.append(("missing-test", path.relative_to(root).as_posix()))
    for path in sorted((root / "schemas").glob("*.schema.json")):
        if path.name not in test_text and path.stem not in test_text:
            findings.append(("uncovered-schema", path.relative_to(root).as_posix()))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate docs/NEXT.md lane invariants and list candidate work.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--roadmap", default=DEFAULT_ROADMAP)
    parser.add_argument("--taskfile", default=DEFAULT_TASKFILE)
    parser.add_argument("--policy", default=DEFAULT_POLICY)
    parser.add_argument("--today", help="override the review date (YYYY-MM-DD)")
    parser.add_argument("--candidates", action="store_true",
                        help="print new work candidates derived from repository state")
    arguments = parser.parse_args(argv)
    try:
        root = arguments.root.resolve()
        roadmap = root / arguments.roadmap
        taskfile = root / arguments.taskfile
        today = dt.date.fromisoformat(arguments.today) if arguments.today else dt.date.today()
        if arguments.candidates:
            findings = collect_candidates(root, root / arguments.policy)
            print(f"roadmap-candidates: {len(findings)}")
            for kind, value in findings:
                print(f"candidate: {kind} {value}")
            return 0
        counts = validate(root, roadmap, taskfile, today)
    except (RoadmapError, OSError, ValueError) as exc:
        print(f"roadmap: fail: {exc}", file=sys.stderr)
        return 2
    print(f"roadmap: pass; actionable={counts['actionable']}; "
          f"gated={counts['gated']}; done={counts['done']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
