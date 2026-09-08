# Dagger CI contract

## Identity

Name: `bima-infra`. Stability: **experimental**. Purpose: execute project-agnostic checks in a pinned GitHub-hosted Dagger environment and return inspectable evidence.

## Entry points

| Function | Output | Scope |
|---|---|---|
| `audit` | directory | repository hygiene result and report |
| `unit-tests` | directory | Python unittest log and exit code |
| `workflow-lint` | directory | actionlint log and exit code |
| `ci` | directory | combined evidence plus `summary.json` |

Hosted invocation:

```bash
dagger api call bima-infra ci --output=.artifacts/dagger-ci
```

## Runner and permissions

- Runner: GitHub-hosted `ubuntu-24.04`.
- Job timeout: 15 minutes.
- Repository permission: `contents: read`.
- Secrets/OIDC: none.
- Local Docker or Dagger installation: not required for this phase.

## Inputs

The module reads the checked-out Dagger workspace. It does not execute project-defined commands or accept secrets. The repository policy remains `.bima/audit.json`.

## Evidence

`ci` returns:

- `audit/result.json` and `audit/report.md`;
- `tests.log` and `tests.exit-code`;
- `actionlint.log` and `actionlint.exit-code`;
- `audit.exit-code`;
- `summary.json`.

The GitHub adapter additionally produces a native audit result and `audit-parity.json`. Parity compares deterministic fields and intentionally excludes `generated_at`.

## Failure contract

Individual commands write their exit code before the module returns its evidence directory. `summary.json` is `pass` only when audit, tests, and workflow lint all return zero. The GitHub adapter uploads available evidence with `if: !cancelled()` and then fails the job when the summary or parity comparison fails. Engine startup, checkout, or catastrophic container failure can prevent evidence generation and must not be treated as success.

## Security and reproducibility

The workflow uses read-only repository permissions and full-SHA-pinned GitHub Actions. Dagger, the base OCI image, Python, and actionlint are pinned. The module runs caller content as audit input plus this repository's fixed regression suite; it does not publish artifacts externally. Credentialed release and deployment operations require separate adapters and contracts.

## Compatibility

The initial contract targets Dagger `v1.0.0-beta.11`. Beta upgrades require an explicit pin update, lockfile review, regression tests, hosted execution, and parity evidence. Azure, GitLab, local Dagger, and self-hosted runners are not supported by this phase.
