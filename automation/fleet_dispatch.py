"""Plan or dispatch one workflow across an explicit repository fleet."""

import argparse
import datetime
import json
import re
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WORKFLOW = re.compile(r"^\.github/workflows/[A-Za-z0-9._-]+\.ya?ml$")
REF = re.compile(r"^[A-Za-z0-9._/-]{1,100}$")
TOP_KEYS = {"schema", "schema_version", "repositories"}
ENTRY_KEYS = {"repository", "workflow"}
EVIDENCE_FIELDS = {"schema", "schema_version", "mode", "ref", "generated_at",
                   "dispatches"}
DISPATCH_FIELDS = {"repository", "workflow", "status", "run_id", "run_url",
                   "error"}
LIMIT_REPOSITORIES = 30
LIMIT_ERROR = 300


class FleetError(RuntimeError):
    """The fleet file or one dispatch is not acceptable."""


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"non-finite number: {value}")


def strict_loads(text):
    return json.loads(text, object_pairs_hook=reject_duplicates,
                      parse_constant=reject_constant)


def load_fleet(path):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise FleetError(f"cannot read fleet file: {exc}") from exc
    try:
        document = strict_loads(text)
    except ValueError as exc:
        raise FleetError(f"invalid JSON in fleet file: {exc}") from exc
    if not isinstance(document, dict) or set(document) != TOP_KEYS:
        raise FleetError(f"fleet keys must be exactly {sorted(TOP_KEYS)}")
    if document["schema"] != "bima-fleet.v1":
        raise FleetError("schema must be bima-fleet.v1")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise FleetError("schema_version must be the integer 1")
    repositories = document["repositories"]
    if not isinstance(repositories, list) or not 1 <= len(repositories) <= LIMIT_REPOSITORIES:
        raise FleetError(f"repositories must contain 1-{LIMIT_REPOSITORIES} entries")
    seen = set()
    for index, entry in enumerate(repositories):
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            raise FleetError(f"entry {index}: keys must be exactly {sorted(ENTRY_KEYS)}")
        repository = entry["repository"]
        if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
            raise FleetError(f"entry {index}: repository must be owner/name")
        if repository.lower() in seen:
            raise FleetError(f"entry {index}: duplicate repository: {repository}")
        seen.add(repository.lower())
        workflow = entry["workflow"]
        if not isinstance(workflow, str) or not WORKFLOW.fullmatch(workflow):
            raise FleetError(
                f"entry {index}: workflow must be .github/workflows/<name>.yml")
    return repositories


def validate_ref(ref):
    if (not REF.fullmatch(ref) or ".." in ref or ref.startswith("-")
            or ref.endswith("/") or "//" in ref):
        raise FleetError("ref must be a branch or tag name without '..', '//' or a leading '-'")
    return ref


def planned(entry):
    return {
        "repository": entry["repository"],
        "workflow": entry["workflow"],
        "status": "planned",
        "run_id": None,
        "run_url": None,
        "error": None,
    }


def newest_dispatch_run(entry):
    """Best-effort run id for the newest manual dispatch of this workflow."""
    command = [
        "gh", "run", "list", "--repo", entry["repository"],
        "--workflow", Path(entry["workflow"]).name,
        "--event", "workflow_dispatch", "--limit", "1",
        "--json", "databaseId,url",
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True,
                                   timeout=60, check=False)
        runs = strict_loads(completed.stdout) if completed.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None
    if not isinstance(runs, list) or not runs or not isinstance(runs[0], dict):
        return None
    run_id = runs[0].get("databaseId")
    url = runs[0].get("url")
    if not isinstance(run_id, int) or not isinstance(url, str) or not url.startswith("https://"):
        return None
    return {"run_id": run_id, "run_url": url}


def dispatch(entry, ref):
    """Trigger one workflow_dispatch and keep the run ids the API returns."""
    before = newest_dispatch_run(entry)
    command = [
        "gh", "api", "--method", "POST",
        f"repos/{entry['repository']}/actions/workflows/"
        f"{Path(entry['workflow']).name}/dispatches",
        "--input", "-",
    ]
    try:
        completed = subprocess.run(
            command, input=json.dumps({"ref": ref}),
            capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {**planned(entry), "status": "failed",
                "error": f"gh could not run: {exc}"[:LIMIT_ERROR]}
    if completed.returncode != 0:
        return {**planned(entry), "status": "failed",
                "error": completed.stderr.strip()[:LIMIT_ERROR] or "gh failed"}
    body = completed.stdout.strip()
    details = {}
    if body:
        try:
            details = strict_loads(body)
        except ValueError:
            details = {}
    if not isinstance(details, dict):
        details = {}
    run_id = details.get("workflow_run_id")
    run_url = details.get("html_url")
    found = {
        "run_id": run_id if isinstance(run_id, int) else None,
        "run_url": run_url if isinstance(run_url, str) and run_url.startswith("https://") else None,
    }
    if found["run_id"] is None:
        # Older API versions answer 204, so look for the new run instead.
        for attempt in range(2):
            current = newest_dispatch_run(entry)
            if current and current["run_id"] != (before or {}).get("run_id"):
                found = current
                break
            if attempt == 0:
                time.sleep(2)
    return {**planned(entry), "status": "dispatched", **found}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Plan or dispatch one workflow across an explicit repository list.")
    parser.add_argument("--fleet", type=Path, default=ROOT / "fleet" / "repos.json")
    parser.add_argument("--ref", default="main")
    parser.add_argument("--apply", action="store_true",
                        help="Dispatch for real; without it the run only prints the plan.")
    parser.add_argument("--output", type=Path, required=True,
                        help="Directory for evidence.json")
    arguments = parser.parse_args(argv)

    try:
        repositories = load_fleet(arguments.fleet)
        ref = validate_ref(arguments.ref)
        if arguments.apply:
            dispatches = [dispatch(entry, ref) for entry in repositories]
        else:
            dispatches = [planned(entry) for entry in repositories]
        evidence = {
            "schema": "bima-fleet-evidence.v1",
            "schema_version": 1,
            "mode": "apply" if arguments.apply else "dry-run",
            "ref": ref,
            "generated_at": datetime.datetime.now(datetime.timezone.utc)
                                     .strftime("%Y-%m-%dT%H:%M:%SZ"),
            "dispatches": dispatches,
        }
        arguments.output.mkdir(parents=True, exist_ok=True)
        (arguments.output / "evidence.json").write_text(
            json.dumps(evidence, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
            encoding="utf-8", newline="\n")
    except (FleetError, OSError) as exc:
        print(f"fleet-dispatch: error: {exc}", file=sys.stderr)
        return 2

    failed = sum(1 for item in dispatches if item["status"] == "failed")
    print(f"fleet-dispatch: {'pass' if not failed else 'fail'}; "
          f"mode={evidence['mode']}; repositories={len(dispatches)}; failed={failed}")
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
