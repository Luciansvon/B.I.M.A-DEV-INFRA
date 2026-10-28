# Fleet dispatch validation — 2026-10-28

Scope: prove that `automation/fleet_dispatch.py` validates the explicit list, writes a dry-run plan without touching GitHub, and really triggers one workflow per repository.

## Dry run

`python -I automation/fleet_dispatch.py --output .artifacts/fleet` printed `fleet-dispatch: pass; mode=dry-run; repositories=2; failed=0`.

Evidence: both entries `planned`, `run_id` and `run_url` null, `ref=main`.

## Real dispatch

`python -I automation/fleet_dispatch.py --apply --output .artifacts/fleet-apply` printed `fleet-dispatch: pass; mode=apply; repositories=2; failed=0`.

| Repository | Workflow | Run | Result |
|---|---|---|---|
| `Luciansvon/AI-COLOR-COMPARE` | `.github/workflows/bima-shared-audit.yml` | [40637742495](https://github.com/Luciansvon/AI-COLOR-COMPARE/actions/runs/40637742495) | `workflow_dispatch`, job `audit / audit` success |
| `Luciansvon/B.I.M.A-DEV-INFRA-FIXTURE` | `.github/workflows/repository-audit.yml` | [40637756778](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA-FIXTURE/actions/runs/40637756778) | `workflow_dispatch`, job `audit / audit` success |

Both evidence entries carry the same run IDs and URLs, and both runs report `event=workflow_dispatch` in the GitHub API, so the dispatch came from this tool rather than from a push.

## Run link resolution

The first `--apply` attempt in this session returned `status=dispatched` with `run_id=null` for both entries. The runs existed (`40637676139`, `40637679469`, created two seconds apart), so the dispatch itself worked but the API answer carried no run details. The tool now records the newest manual dispatch before the call and compares afterwards, which produced the run links in the table above.

## Local verification

- `python -I -m unittest discover -s tests -p "test_fleet_dispatch.py"`: 6 tests, OK.
- zizmor on the modified `ci.yml`: no findings.
- Hosted run `40638462572`: 190 tests per OS, `fleet-dispatch: pass; mode=dry-run; repositories=2; failed=0` on Ubuntu and Windows, repository audit 204 files / 0 findings, and the `fleet/evidence.json` artifact retained.

## Boundaries

- The dispatch proves GitHub accepted a `workflow_dispatch` for that workflow file; it does not prove the consumer's pinned infrastructure version is the current one.
- The dispatched audit runs succeeded, but their artifacts were not downloaded or compared here.
- CI only runs the dry-run plan; hosted `--apply` needs a token with `Actions: write` on the target repositories, which is not configured.
