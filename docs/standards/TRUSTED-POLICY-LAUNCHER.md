# Trusted policy launcher v1

Status: **Hosted proof passed for the reusable workflow bytes now pinned (runs `34707376819`, `34767472911`, `40622237968`, `40625331457`). No consumer pin changed.** The check `Trusted repository audit proof / audit` is a required merge context on `main`.

The reusable workflow checks out the caller as an untrusted subject and DEV-INFRA at the exact called-workflow SHA as trusted infrastructure. The launcher accepts no actor, policy hash, subject revision, operation or resource scope from workflow inputs. It derives them from runner identity, Git state, the trusted bundle and the project declaration.

```text
caller checkout + .bima/project.json
                 |
exact DEV-INFRA workflow SHA + trusted bundle/policy hash
                 |
                 v
trusted launcher -> Policy Gate -> repository audit -> evidence
```

Required runtime identity is `BIMA_TRUSTED_ACTOR`, `BIMA_SUBJECT_REPOSITORY`, `BIMA_WORKFLOW_REPOSITORY`, `BIMA_WORKFLOW_REF`, `BIMA_WORKFLOW_SHA`, `BIMA_RUN_ID` and `BIMA_RUN_ATTEMPT`. The reusable workflow also derives `BIMA_EVENT_NAME` and `BIMA_BASE_SHA` from the GitHub event; neither is a `workflow_call` input. The infrastructure checkout must be clean, separate from the subject, and at the full workflow SHA. The workflow reference must equal `<repository>/<workflow-path>@<sha>`.

For `pull_request` runs, the subject checkout keeps full history so the launcher can read the base commit. The launcher refuses an unknown or non-ancestor base, validates the base project declaration, rejects a changed `audit_policy` path, and runs the audit against the exact base policy bytes. Push, schedule and manual runs keep using the checked-out policy. A policy change therefore takes effect only after a separate merged pull request.

The checked-in trust bundle pins the workflow repository/path, policy path/hash, operation and decision TTL. The reusable workflow hardcodes this bundle ID; it is not a caller input. The subject can narrow its audit timeout/output policy but cannot select a different trusted bundle or elevate network, credentials, command or attempts.

The reusable workflow uses read-only contents permission, explicit checkout paths, detached credential persistence, a 10-minute job timeout and bounded uploaded evidence. A denial writes launcher evidence and never launches the verifier. `ALLOW` still authorizes only `repository-audit.v1`; it is not release, patch, retry or shell-command authority.

Local adversarial tests cover subject policy shadowing, scope elevation, workflow-ref substitution, policy tampering, repository spoofing, overlapping checkouts, base-policy selection, deleted required files and policy-path switching. Hosted proof at reusable-workflow SHA `1103ac3978441253251a9a818a4977fbdbdb350a` passed in run `34707376819` and again with the caller at `main` `4ebd5df` in run `34767472911`; Infrastructure CI run `34767472551` also passed. The proof then pinned `67736411bf55c4d7b1559b3f473a2da8f92475ba` for run `40622237968`, which returned `ALLOW` and a passing 171-file subject audit at fixture revision `53307aa82437511588fefa0d102228bfb5dd35d4`. After the base-policy change, the proof pins `49e7424e88f2512d4a5ef753730e6dfe293a8fbd`; run `40625331457` returned launcher/policy `ALLOW`, `verifier_launched=true`, and a passing 171-file audit whose `policy_sha256` `0097cf83...` equals the base `.bima/audit.json`. The proof covers this workflow and checked-in policy only: a consumer must adopt its own pinned reference and pass its own compatibility run.

GitHub.com documents `job.workflow_repository`, `job.workflow_ref` and `job.workflow_sha` for reusable-workflow identity. Actionlint 1.7.12 predates those fields, so `.github/actionlint.yaml` suppresses only its exact unknown-property diagnostic for this workflow; all other lint checks remain active.
