"""Render a static workflow-status dashboard from the catalog and latest runs."""

import argparse
import datetime
import html
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
STATUSES = {"experimental", "beta", "stable"}
CONCLUSIONS = {"success", "failure", "skipped", "cancelled", "timed_out",
               "action_required", "neutral", "stale"}
RUN_STATUSES = {"queued", "in_progress", "completed", "waiting", "pending",
                "requested"}
TOP_KEYS = {"schema", "schema_version", "repository", "branch", "generated_at", "workflows"}
RUN_KEYS = {"status", "conclusion", "created_at", "url"}
CATALOG_KEYS = {"id", "path", "status", "docs", "consumers", "sha256", "summary"}
LIMITS = {"workflows": 50, "summary": 200, "url": 500}


class DashboardError(RuntimeError):
    """The dashboard inputs are incomplete or inconsistent."""


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


def load_json(path, label):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise DashboardError(f"cannot read {label}: {exc}") from exc
    try:
        return strict_loads(text)
    except ValueError as exc:
        raise DashboardError(f"invalid JSON in {label}: {exc}") from exc


def discover_workflows(directory):
    try:
        entries = sorted(directory.iterdir())
    except OSError as exc:
        raise DashboardError(f"cannot read workflows directory: {exc}") from exc
    files = []
    for path in entries:
        if path.is_symlink() or not path.is_file() or path.suffix not in {".yml", ".yaml"}:
            continue
        files.append(path.name)
    if not 1 <= len(files) <= LIMITS["workflows"]:
        raise DashboardError("workflows directory must contain 1-50 YAML files")
    return files


def load_catalog(path):
    document = load_json(path, "catalog")
    workflows = document.get("workflows") if isinstance(document, dict) else None
    if not isinstance(workflows, list) or not 1 <= len(workflows) <= LIMITS["workflows"]:
        raise DashboardError("catalog must contain 1-50 workflows")
    catalog = {}
    for entry in workflows:
        if not isinstance(entry, dict) or set(entry) != CATALOG_KEYS:
            raise DashboardError("catalog entry shape is invalid")
        identifier = entry["id"]
        if not isinstance(identifier, str) or identifier in catalog:
            raise DashboardError(f"invalid or duplicate workflow id: {identifier!r}")
        if entry["status"] not in STATUSES:
            raise DashboardError(f"{identifier}: invalid status")
        if not isinstance(entry["summary"], str) or len(entry["summary"]) > LIMITS["summary"]:
            raise DashboardError(f"{identifier}: invalid summary")
        if not isinstance(entry["consumers"], list) or not all(
                isinstance(item, str) for item in entry["consumers"]):
            raise DashboardError(f"{identifier}: invalid consumers")
        catalog[identifier] = entry
    return catalog


def normalize_run(run):
    """gh reports an empty conclusion while a run is not finished yet."""
    return {
        "status": run.get("status"),
        "conclusion": run.get("conclusion") or None,
        "created_at": run.get("createdAt"),
        "url": run.get("url"),
    }


def missing_workflow(stderr):
    """gh reports 404 when a workflow file is not yet on the default branch."""
    return "HTTP 404" in stderr and "not found on the default branch" in stderr


def fetch_runs(repository, branch, files):
    if not REPOSITORY.fullmatch(repository):
        raise DashboardError("repository must be owner/name")
    workflows = {}
    for name in files:
        command = ["gh", "run", "list", "--repo", repository,
                   "--workflow", name, "--branch", branch,
                   "--limit", "1", "--json",
                   "databaseId,status,conclusion,createdAt,url"]
        try:
            completed = subprocess.run(command, capture_output=True, text=True,
                                       timeout=60, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DashboardError(f"gh could not run for {name}: {exc}") from exc
        if completed.returncode != 0:
            if missing_workflow(completed.stderr):
                continue
            raise DashboardError(
                f"gh failed for {name}: {completed.stderr.strip()[:300]}")
        try:
            runs = strict_loads(completed.stdout)
        except ValueError as exc:
            raise DashboardError(f"gh returned invalid JSON for {name}") from exc
        if not isinstance(runs, list):
            raise DashboardError(f"gh returned a non-list for {name}")
        if runs:
            workflows[name] = normalize_run(runs[0])
    return {
        "schema": "bima-dashboard-status.v1",
        "schema_version": 1,
        "repository": repository,
        "branch": branch,
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
                                 .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "workflows": workflows,
    }


def validate_runs(document, files):
    if not isinstance(document, dict) or set(document) != TOP_KEYS:
        raise DashboardError(f"runs keys must be exactly {sorted(TOP_KEYS)}")
    if document["schema"] != "bima-dashboard-status.v1":
        raise DashboardError("runs schema must be bima-dashboard-status.v1")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise DashboardError("runs schema_version must be the integer 1")
    if not isinstance(document["repository"], str) or not REPOSITORY.fullmatch(document["repository"]):
        raise DashboardError("runs repository must be owner/name")
    if not isinstance(document["branch"], str) or not 1 <= len(document["branch"]) <= 100:
        raise DashboardError("runs branch is invalid")
    if not isinstance(document["generated_at"], str) or not document["generated_at"]:
        raise DashboardError("runs generated_at is invalid")
    workflows = document["workflows"]
    if not isinstance(workflows, dict):
        raise DashboardError("runs workflows must be an object")
    for name, run in workflows.items():
        if name not in files:
            raise DashboardError(f"runs contain an unknown workflow file: {name}")
        if not isinstance(run, dict) or set(run) != RUN_KEYS:
            raise DashboardError(f"{name}: run shape is invalid")
        if run["status"] is not None and run["status"] not in RUN_STATUSES:
            raise DashboardError(f"{name}: invalid run status")
        if run["conclusion"] is not None and run["conclusion"] not in CONCLUSIONS:
            raise DashboardError(f"{name}: invalid conclusion")
        if not isinstance(run["created_at"], str) or len(run["created_at"]) > 40:
            raise DashboardError(f"{name}: invalid created_at")
        url = run["url"]
        if not isinstance(url, str) or len(url) > LIMITS["url"] or not url.startswith("https://"):
            raise DashboardError(f"{name}: invalid run URL")
    return document


def badge(conclusion, status):
    if status != "completed" or conclusion is None:
        if status in {"queued", "in_progress", "waiting", "pending", "requested"}:
            return "in progress", "pending"
        return "unknown", "pending"
    return conclusion.replace("_", " "), conclusion


def render_runs(repository, branch, files, runs):
    counts = {"success": 0, "failure": 0, "other": 0, "missing": 0}
    rows = []
    for name in files:
        run = runs["workflows"].get(name)
        if run is None:
            label, css = "no direct runs", "missing"
            counts["missing"] += 1
            updated = "&mdash;"
            link = "&mdash;"
        else:
            label, css = badge(run["conclusion"], run["status"])
            if css == "success":
                counts["success"] += 1
            elif css == "failure":
                counts["failure"] += 1
            else:
                counts["other"] += 1
            updated = html.escape(run["created_at"] or "unknown")
            link = f'<a href="{html.escape(run["url"], quote=True)}">latest run</a>'
        source = (f"https://github.com/{repository}/blob/{branch}/.github/workflows/"
                  f"{name}")
        rows.append(
            "<tr>"
            f'<td><a href="{html.escape(source, quote=True)}"><code>{html.escape(name)}</code></a></td>'
            f'<td><span class="badge {css}">{html.escape(label)}</span></td>'
            f"<td>{updated}<br>{link}</td>"
            "</tr>")
    return f"""<h2>Repository workflows</h2>
<p class="meta">Latest run on branch <code>{html.escape(branch)}</code>. Reusable-only workflows have no direct runs and stay listed as such.</p>
<div class="summary-grid">
<div class="metric"><strong>{len(files)}</strong><span>workflows</span></div>
<div class="metric"><strong>{counts["success"]}</strong><span>latest run passed</span></div>
<div class="metric"><strong>{counts["failure"]}</strong><span>latest run failed</span></div>
<div class="metric"><strong>{counts["missing"]}</strong><span>no direct runs</span></div>
</div>
<table>
<thead><tr><th>Workflow</th><th>Latest</th><th>Updated</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>"""


def render_catalog(catalog, repository, branch):
    rows = []
    for identifier, entry in catalog.items():
        consumers = ", ".join(html.escape(item) for item in entry["consumers"]) or "none"
        docs = (f"https://github.com/{repository}/blob/{branch}/{entry['docs']}")
        rows.append(
            "<tr>"
            f'<td><a href="{html.escape(docs, quote=True)}">{html.escape(identifier)}</a>'
            f'<div class="summary">{html.escape(entry["summary"])}</div></td>'
            f'<td><span class="badge {html.escape(entry["status"])}">{html.escape(entry["status"])}</span></td>'
            f"<td>{consumers}</td>"
            f'<td><code>{html.escape(entry["path"])}</code></td>'
            "</tr>")
    return f"""<h2>Reusable workflow catalog</h2>
<p class="meta">Reviewed reusable workflows. Their runs appear under the caller workflows, not under these files.</p>
<table>
<thead><tr><th>Workflow</th><th>Status</th><th>Proven consumers</th><th>Path</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>"""


def render(catalog, files, runs):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>B.I.M.A-DEV-INFRA workflow status</title>
<style>
:root {{ color-scheme: light dark; --bg:#faf9f7; --fg:#1c1b19; --muted:#5f5b55; --line:#d9d5cf; --card:#ffffff; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#161513; --fg:#f2efe9; --muted:#b3ada4; --line:#3a3732; --card:#1f1d1a; }} }}
* {{ box-sizing: border-box; }}
body {{ margin:0; padding:2rem 1rem; background:var(--bg); color:var(--fg); font:15px/1.5 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width: 1150px; margin: 0 auto; }}
h1 {{ font-size: clamp(1.5rem, 3vw, 2.2rem); margin: 0 0 .25rem; letter-spacing: -.02em; }}
h2 {{ font-size: 1.1rem; margin: 2rem 0 .35rem; }}
p.meta {{ color: var(--muted); margin: 0 0 1.25rem; }}
.summary-grid {{ display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.25rem; }}
.metric {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:.75rem 1rem; min-width:120px; }}
.metric strong {{ display:block; font-size:1.5rem; }}
.metric span {{ color:var(--muted); font-size:.85rem; }}
table {{ width:100%; border-collapse:collapse; background:var(--card); border:1px solid var(--line); border-radius:10px; overflow:hidden; }}
th, td {{ text-align:left; padding:.7rem .75rem; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }}
tr:last-child td {{ border-bottom:0; }}
code {{ font-size:.8rem; word-break:break-all; }}
.summary {{ color:var(--muted); font-size:.85rem; margin-top:.2rem; max-width:40rem; }}
.badge {{ display:inline-block; padding:.15rem .55rem; border-radius:999px; font-size:.8rem; font-weight:600; border:1px solid var(--line); }}
.badge.success {{ background:#e4f4e8; color:#14532d; border-color:#a7d8b4; }}
.badge.failure {{ background:#fbe4e4; color:#7f1d1d; border-color:#e8b4b4; }}
.badge.pending {{ background:#fdf1d6; color:#713f12; border-color:#e8cf9a; }}
.badge.missing {{ background:#eeece8; color:#4b4740; border-color:#cfc9c0; }}
.badge.experimental, .badge.beta, .badge.stable, .badge.skipped, .badge.cancelled, .badge.neutral, .badge.stale, .badge.action_required, .badge.timed_out {{ background:#eeece8; color:#4b4740; border-color:#cfc9c0; }}
a {{ color:inherit; }}
footer {{ color:var(--muted); font-size:.8rem; margin-top:1.5rem; }}
</style>
</head>
<body>
<main>
<h1>B.I.M.A-DEV-INFRA workflow status</h1>
<p class="meta">{html.escape(runs["repository"])} &middot; branch <code>{html.escape(runs["branch"])}</code> &middot; generated {html.escape(runs["generated_at"])}</p>
{render_runs(runs["repository"], runs["branch"], files, runs)}
{render_catalog(catalog, runs["repository"], runs["branch"])}
<footer>Latest run per repository workflow, read from the GitHub API. This page keeps no history and is not a monitoring or alerting system.</footer>
</main>
</body>
</html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Render the workflow-status dashboard.")
    parser.add_argument("--catalog", type=Path, default=ROOT / "catalog" / "workflows.json")
    parser.add_argument("--workflows-dir", type=Path, default=ROOT / ".github" / "workflows")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repository")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--runs", type=Path)
    parser.add_argument("--fetch", action="store_true")
    arguments = parser.parse_args(argv)

    try:
        catalog = load_catalog(arguments.catalog)
        files = discover_workflows(arguments.workflows_dir)
        if arguments.fetch:
            if not arguments.repository:
                raise DashboardError("--repository is required with --fetch")
            runs = fetch_runs(arguments.repository, arguments.branch, files)
        elif arguments.runs:
            runs = load_json(arguments.runs, "runs")
        else:
            raise DashboardError("pass --runs or --fetch")
        validate_runs(runs, files)

        arguments.output_dir.mkdir(parents=True, exist_ok=True)
        (arguments.output_dir / "index.html").write_text(
            render(catalog, files, runs), encoding="utf-8", newline="\n")
        (arguments.output_dir / "status.json").write_text(
            json.dumps(runs, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
            encoding="utf-8", newline="\n")
    except (DashboardError, OSError) as exc:
        print(f"dashboard: fail: {exc}", file=sys.stderr)
        return 2

    print(f"dashboard: pass; workflows={len(files)}; "
          f"missing={len(files) - len(runs['workflows'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
