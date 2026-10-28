# Workflow status dashboard

Status: **experimental**. A static snapshot of the latest workflow runs; it is not monitoring, alerting or a historical record.

## Identity

`automation/dashboard.py` renders `index.html` and `status.json` from three inputs:

- `.github/workflows/` — the workflow files that should be listed;
- `catalog/workflows.json` — the reusable workflow catalog and its review status;
- the GitHub API — the latest run per workflow file on one branch.

`.github/workflows/dashboard.yml` runs it on pull requests (build only), on pushes to `main`, daily at 03:17 UTC, and on manual dispatch. Pages deploys only outside pull requests.

## How a workflow is located

The dashboard lists every `*.yml`/`*.yaml` file in the workflows directory and asks `gh run list --workflow <file name>` for its newest run on the branch. GitHub tracks runs per workflow file, so a workflow file that nobody calls directly shows `no direct runs`.

That is the normal state for the four reusable workflows: they run *inside* a caller's run and never get a run of their own. Their review status and proven consumers come from the catalog table instead of from run data.

A `HTTP 404 ... not found on the default branch` answer means the file is not registered on the default branch yet — for example a workflow added in the pull request being built. It is rendered as `no direct runs`, not as a failure. Any other `gh` error fails the build closed.

## Output contract

`status.json`:

```json
{
  "schema_version": 1,
  "repository": "owner/name",
  "branch": "main",
  "generated_at": "2026-10-28T05:05:24Z",
  "workflows": {
    "ci.yml": {
      "status": "completed",
      "conclusion": "success",
      "created_at": "2026-10-28T05:01:51Z",
      "url": "https://github.com/owner/name/actions/runs/1"
    }
  }
}
```

`workflows` only contains files that have a run; a missing key means no run on that branch. `status.json` is written in canonical JSON (sorted keys, two-space indent).

## Failure contract

The command exits `2` and writes nothing when:

- the catalog is unreadable, has a duplicate or invalid ID, an unknown entry field, an invalid status, summary or consumers list;
- the workflows directory is empty, unreadable or holds more than 50 YAML files;
- `--fetch` is used without `--repository`;
- neither `--runs` nor `--fetch` is given;
- `gh` fails for a reason other than a file that is not yet on the default branch;
- a run record has an unknown workflow file, an invalid status, conclusion, timestamp or URL.

Exit `0` prints `dashboard: pass; workflows=<n>; missing=<n>` where `missing` counts files without a direct run.

## Boundaries

- It shows the newest run per file, not a trend, duration or flake history.
- It does not read artifacts, job logs, annotations or branch protection results.
- It does not verify that a consumer actually ran a reusable workflow; catalog consumers stay a documented, human-checked claim.
- It does not alert anyone. A failed run stays on the page until the next scheduled render.
- The page is public. It contains workflow names, run links and catalog metadata only — never secrets or logs.

## Self-test

`tests/test_dashboard.py` covers the rendered page (missing run, escaped summary, absolute documentation links), rejection of an unknown workflow file, ignoring non-YAML files, and the 404-versus-real-failure distinction.
