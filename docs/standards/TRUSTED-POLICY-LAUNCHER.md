# Trusted policy launcher v1

## Identity

Name: `trusted-repository-audit`. Stability: **beta**.

The reusable workflow checks out the caller as an untrusted subject and DEV-INFRA at the exact called-workflow SHA as trusted infrastructure. The launcher accepts no actor, policy hash, subject revision, operation or resource scope from workflow inputs. It derives them from runner identity, Git state, the trusted bundle and the project declaration. Implementation: [`automation/trusted_policy_launcher.py`](../../automation/trusted_policy_launcher.py); reusable entry point: [workflow](../../.github/workflows/trusted-repository-audit.yml).

Hosted proof passed for the reusable workflow bytes now pinned (runs `34707376819`, `34767472911`, `40622237968`, `40625331457`). No consumer pin changed. The check `Trusted repository audit proof / audit` is a required merge context on `main`.

## Triggers

The reusable workflow is invoked only through `workflow_call`. The in-repository proof workflow calls it on pushes to `main`, pull requests and manual dispatch. `ci.yml` also self-calls it on every push to `main` and every pull request, plus manual dispatch. There is no direct API or repository-dispatch trigger.

## Inputs

| Name | Required | Type | Default | Purpose |
|---|---|---|---|---|
| `project-path` | no | string | `.bima/project.json` | Subject-relative `bima-project.v1` declaration |
| `artifact-name` | no | string | `trusted-repository-audit` | Unique evidence artifact prefix per call |

Neither input selects the actor, revision, trusted bundle, operation or resource scope.

## Outputs

| Name | Type | Purpose |
|---|---|---|
| `artifact-id` | string | Uploaded decision and audit evidence artifact ID |

```text
caller checkout + .bima/project.json
                 |
exact DEV-INFRA workflow SHA + trusted bundle/policy hash
                 |
                 v
trusted launcher -> Policy Gate -> repository audit -> evidence
```

## Runner

GitHub-hosted Ubuntu 24.04 with Git, Bash and pinned Python 3.13.15. No self-hosted labels, hardware, device or network service is required. The workflow runs in the caller's repository context but checks out the two repositories into separate paths.

## Permissions

`contents: read` only. No OIDC, secrets, write token, `pull_request_target` or external credentials. Both checkouts use `persist-credentials: false`. The caller cannot add permissions that the reusable workflow does not request.

## Execution limits

Ten-minute job timeout per call. The launcher and verifier use the operation timeout from the subject project declaration, which is 120 seconds in this repository. The decision window is 30 to 600 seconds. There is no retry loop; the caller owns cancellation and run attempts are part of the request identity.

## Evidence

Every run writes `decision.json` plus the Policy Gate decision and the repository-audit `result.json` and `report.md`. The workflow uploads them as one artifact with `if-no-files-found: error` and 14-day retention. A denial still writes launcher evidence; `ALLOW` records `verifier_launched=true` only after the verifier actually runs.

## Failure contract

The launcher exits `0` for a passing audit, `1` for audit findings, `2` for an audit or launcher error, and `3` for a denied trust boundary. A denial writes a `DENY` decision and never launches the verifier. An `ALLOW` decision that launches a failing verifier does not become a pass: the workflow propagates the verifier exit code.

## Security

Required runtime identity is `BIMA_TRUSTED_ACTOR`, `BIMA_SUBJECT_REPOSITORY`, `BIMA_WORKFLOW_REPOSITORY`, `BIMA_WORKFLOW_REF`, `BIMA_WORKFLOW_SHA`, `BIMA_RUN_ID` and `BIMA_RUN_ATTEMPT`. The reusable workflow also derives `BIMA_EVENT_NAME` and `BIMA_BASE_SHA` from the GitHub event; neither is a `workflow_call` input. The infrastructure checkout must be clean, separate from the subject, and at the full workflow SHA. The workflow reference must equal `<repository>/<workflow-path>@<sha>`.

For `pull_request` runs, the subject checkout keeps full history so the launcher can read the base commit. The launcher refuses an unknown or non-ancestor base, validates the base project declaration, rejects a changed `audit_policy` path, and runs the audit against the exact base policy bytes. Push, schedule and manual runs keep using the checked-out policy. A policy change therefore takes effect only after a separate merged pull request.

The checked-in trust bundle pins the workflow repository/path, policy path/hash, operation and decision TTL. The reusable workflow hardcodes this bundle ID; it is not a caller input. The subject can narrow its audit timeout/output policy but cannot select a different trusted bundle or elevate network, credentials, command or attempts.

Local adversarial tests cover subject policy shadowing, scope elevation, workflow-ref substitution, policy tampering, repository spoofing, overlapping checkouts, base-policy selection, deleted required files and policy-path switching. The module treats the caller checkout as data and does not execute caller scripts. A malicious infrastructure SHA is still a review boundary: consumers must review the exact pin they adopt.

## Compatibility

Changes to inputs, decision fields, exit codes or the trust-bundle schema require an ADR, updated regression fixtures and a re-pin of every caller. `ALLOW` authorizes only `repository-audit.v1`; it is not release, patch, retry or shell-command authority. Hosted proof at reusable-workflow SHA `1103ac3978441253251a9a818a4977fbdbdb350a` passed in run `34707376819` and again with the caller at `main` `4ebd5df` in run `34767472911`; Infrastructure CI run `34767472551` also passed. The proof then pinned `67736411bf55c4d7b1559b3f473a2da8f92475ba` for run `40622237968`, which returned `ALLOW` and a passing 171-file subject audit at fixture revision `53307aa82437511588fefa0d102228bfb5dd35d4`. After the base-policy change, the proof pinned `49e7424e88f2512d4a5ef753730e6dfe293a8fbd`; run `40625331457` returned launcher/policy `ALLOW`, `verifier_launched=true`, and a passing 171-file audit whose `policy_sha256` `0097cf83...` equals the base `.bima/audit.json`. The roadmap expansion re-pins the proof to `2393301dd53106c4786ad2bf3f10e394346cddb2` so the verifier accepts the expanded 132-file policy; the hosted run for that pin is pending. The proof covers this workflow and checked-in policy only: a consumer must adopt its own pinned reference and pass its own compatibility run.

GitHub.com documents `job.workflow_repository`, `job.workflow_ref` and `job.workflow_sha` for reusable-workflow identity. Actionlint 1.7.12 predates those fields, so `.github/actionlint.yaml` suppresses only its exact unknown-property diagnostic for this workflow; all other lint checks remain active.

## Self-call

`ci.yml` calls this reusable workflow through the `Trusted repository audit self-call` job on every push to `main` and every pull request, plus manual dispatch. The job grants only `contents: read`, passes only `artifact-name: trusted-self-audit`, and adds no secrets, write permissions, `pull_request_target` or `continue-on-error`. It exercises the launcher as a real in-repository caller, so the workflow stays covered outside its proof workflow; the job duplicates none of the launcher's base-policy or revision logic. Hosted proof of a launcher run stays in the separate proof runs listed in Identity; this document does not yet record a hosted self-call CI run.
