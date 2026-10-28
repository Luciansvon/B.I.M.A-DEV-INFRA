# Repository fleet dispatch

Status: **experimental**. One explicit list, one workflow, no organization discovery.

## Identity

`fleet/repos.json` lists the repositories to trigger. `automation/fleet_dispatch.py` validates that list and either prints the plan or sends one `workflow_dispatch` per entry.

## List contract

The file has exactly `schema_version` (integer `1`) and `repositories` (1–30 entries). Each entry has exactly:

| Field | Meaning |
|---|---|
| `repository` | `owner/name` |
| `workflow` | `.github/workflows/<name>.yml`; must stay inside that directory |

Repositories must be unique, case-insensitively. Unknown fields, a duplicate repository, an unsafe path or an out-of-range list fail before anything is dispatched.

Every entry names its own workflow file, because consumers do not have to use the template's file name.

## Usage

```bash
# Plan only; touches nothing outside the local evidence file.
python -I automation/fleet_dispatch.py --output .artifacts/fleet

# Trigger the real dispatch.
python -I automation/fleet_dispatch.py --apply --output .artifacts/fleet-apply
```

`--ref` defaults to `main`. A ref may not contain `..`, `//`, a trailing `/` or a leading `-`.

Without `--apply` the tool never calls GitHub.

## Evidence

`<output>/evidence.json`:

```json
{
  "schema_version": 1,
  "mode": "dry-run",
  "ref": "main",
  "generated_at": "2026-10-28T05:23:43Z",
  "dispatches": [
    {
      "repository": "Luciansvon/AI-COLOR-COMPARE",
      "workflow": ".github/workflows/bima-shared-audit.yml",
      "status": "dispatched",
      "run_id": 40637742495,
      "run_url": "https://github.com/Luciansvon/AI-COLOR-COMPARE/actions/runs/40637742495",
      "error": null
    }
  ]
}
```

`status` is `planned`, `dispatched` or `failed`. A dispatch that GitHub accepts is reported as `dispatched` even when the run link could not be resolved; that is why `run_id` and `run_url` are nullable.

The command exits `2` when the list or ref is invalid, or when any entry failed. One failed repository does not stop the rest, and the evidence keeps every result.

## Run link resolution

The dispatch call sends the ref as a JSON body. Newer API versions answer `200` with `workflow_run_id` and `html_url`, which are recorded directly. Older versions answer `204` with no body; then the tool records the newest manual dispatch before the call, looks again after it, retries once after two seconds, and attaches the run only if the identifier changed. If no new run appears, the dispatch stays recorded without a link.

## Permissions

The token needs `Actions: write` on every listed repository. The `GITHUB_TOKEN` inside a workflow is scoped to the repository that runs the workflow, so a hosted `--apply` would need a user-owned fine-grained token stored as a secret. That secret is deliberately not configured: CI runs only the dry-run plan, and the real dispatch is an operator action with their own token.

## Boundaries

- It does not discover repositories from an organization; the list is the whole scope.
- It does not add, remove or archive repositories, or update their workflow pins.
- It does not retry a failed dispatch, wait for a run to finish, or collect the run's result.
- It does not prove that a consumer actually used the expected workflow version; only that GitHub accepted a dispatch of that file.

## Self-test

`tests/test_fleet_dispatch.py` covers the plan evidence, duplicate repositories, unknown entries, unsafe workflow paths, an empty list and unsafe refs. CI runs the dry-run plan on Ubuntu and Windows and keeps `evidence.json`.
