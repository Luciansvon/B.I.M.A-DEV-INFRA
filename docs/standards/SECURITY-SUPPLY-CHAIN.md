# Security and supply-chain workflow template

Status: **experimental**. Caller pins a reviewed DEV-INFRA commit; the template itself is not a security guarantee.

## Identity

Name: `.github/workflows/security-supply-chain.yml`. Purpose: run the reviewed workflow-hardening checks and pull-request dependency review against a consumer repository without copying YAML.

The template packages:

- action-validator v0.9.0 for workflow and local Action schema/path-glob errors;
- pinact v4.1.1 for full-SHA Action and reusable-workflow references;
- zizmor v1.31.1 for offline workflow, local Action and Dependabot findings;
- `actions/dependency-review-action` v5.0.0 for pull-request dependency and vulnerability changes.

Tool versions and SHA-256 digests live in `automation/install_security_tools.sh`. The same installer is used by DEV-INFRA CI.

## Triggers

`workflow_call` only. The caller chooses its own events. `pull_request` is required for dependency review; `push` and `workflow_dispatch` run only the workflow-security job. Manual/API invocation is allowed through the caller.

## Inputs

| Input | Required | Type | Default | Description |
|---|---:|---|---|---|
| `artifact-name` | no | string | `security-supply-chain` | Unique evidence artifact prefix per call |
| `dependency-review` | no | boolean | `true` | Run dependency review on pull requests; disable only when the caller has no dependency manifests, dependency graph or GHAS |

## Outputs

| Output | Type | Description |
|---|---|---|
| `artifact-id` | string | Uploaded security evidence artifact ID |

## Runner

GitHub-hosted `ubuntu-24.04`, no labels or hardware requirements. action-validator has no official Windows binary, so this template is Linux-only.

## Permissions

`contents: read` only. No secrets, OIDC, write scope or `pull-requests: write`. Dependency review comments are disabled; findings remain in the check and job summary.

## Execution limits

- workflow-security: 10 minutes.
- dependency-review: 10 minutes.
- No retries, concurrency group or self-hosted runner.

## Evidence

The workflow uploads `summary.txt` plus one log per tool. `summary.txt` records tool versions, selected workflow/action counts, Dependabot presence and final status. Artifacts are retained for 14 days even when a check fails. DEV-INFRA CI calls this template on every push and pull request as a hosted self-test.

## Failure contract

- Any action-validator, pinact or zizmor finding fails the job.
- Missing selected workflow inputs fail closed.
- Dependency review fails on runtime-scope vulnerabilities at `high` or `critical`; the action's own failure fails the job.
- Dependency review is skipped on non-`pull_request` events and when `dependency-review` is `false`. A skip is visible in the check list, not converted to a pass claim for that scope.

## Security

- The caller checkout is untrusted data in `subject`; the template never executes consumer workflow or application code.
- The infrastructure checkout uses `job.workflow_repository` and `job.workflow_sha`, not caller inputs.
- Both checkouts set `persist-credentials: false`.
- Every tool download is fixed-version and SHA-256 verified before execution.
- pinact runs `--fix=false --no-api`; zizmor runs `--offline --strict-collection`; no automatic fix or remote API call.
- The dependency-review job reads GitHub's dependency graph through the Action; it receives no repository write token.

## Compatibility

Callers pin a full DEV-INFRA commit SHA in `uses:`; the template reads `job.workflow_repository` and `job.workflow_sha` for its own infrastructure checkout, so the same reviewed revision supplies both the workflow and the installer. `dependency-review-action` v5 requires Actions Runner v2.327.1 or newer; GitHub-hosted runners satisfy this. Dependency review requires a public repository or a private repository with GitHub Advanced Security plus the dependency graph enabled, and at least one supported dependency manifest. Set `dependency-review: false` only when one of those prerequisites is unavailable, and record the missing coverage; do not treat the skip as a passing dependency review.

A template change follows the normal pin update: checksum review, local/CI self-test, hosted run, then consumer pin updates.

## Boundaries

Pinact proves only that a full SHA is present, not that it belongs to the named repository or meets a release-age/provenance policy. zizmor runs offline, so online-only audits remain absent. action-validator validates structure and path globs, not shell behavior or runtime safety. Dependency review covers dependency changes on pull requests, not the full history, application source, secrets, CodeQL, SBOM generation or release provenance. This template does not replace those gates.

## Self-test

`ci.yml` calls `./.github/workflows/security-supply-chain.yml` on push, pull request and manual dispatch. The call stays workspace-relative because actionlint v1.7.12 cannot parse GitHub's `$/` self-repository syntax; a narrow `zizmor: ignore[self-repository]` records that tool limit. The self-test proves action-validator, pinact and zizmor against this repository's own workflows, local Action and Dependabot configuration.

DEV-INFRA has no dependency manifests, so its dependency graph is empty and dependency review has nothing to compare. The self-test therefore passes `dependency-review: false` and does not claim that scope as proven. The dependency-review job is hosted-proven only when a consumer with at least one supported manifest calls this template.
