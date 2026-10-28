# Trusted policy launcher v1

Status: **Hosted proof passed for the reusable workflow bytes now pinned (runs `34707376819`, `34767472911`); the new pin's hosted run is pending. No consumer pin changed.** The check `Trusted repository audit proof / audit` is a required merge context on `main`.

The reusable workflow checks out the caller as an untrusted subject and DEV-INFRA at the exact called-workflow SHA as trusted infrastructure. The launcher accepts no actor, policy hash, subject revision, operation or resource scope from workflow inputs. It derives them from runner identity, Git state, the trusted bundle and the project declaration.

```text
caller checkout + .bima/project.json
                 |
exact DEV-INFRA workflow SHA + trusted bundle/policy hash
                 |
                 v
trusted launcher -> Policy Gate -> repository audit -> evidence
```

Required runtime identity is `BIMA_TRUSTED_ACTOR`, `BIMA_SUBJECT_REPOSITORY`, `BIMA_WORKFLOW_REPOSITORY`, `BIMA_WORKFLOW_REF`, `BIMA_WORKFLOW_SHA`, `BIMA_RUN_ID` and `BIMA_RUN_ATTEMPT`. The infrastructure checkout must be clean, separate from the subject, and at the full workflow SHA. The workflow reference must equal `<repository>/<workflow-path>@<sha>`.

The checked-in trust bundle pins the workflow repository/path, policy path/hash, operation and decision TTL. The reusable workflow hardcodes this bundle ID; it is not a caller input. The subject can narrow its audit timeout/output policy but cannot select a different trusted bundle or elevate network, credentials, command or attempts.

The reusable workflow uses read-only contents permission, explicit checkout paths, detached credential persistence, a 10-minute job timeout and bounded uploaded evidence. A denial writes launcher evidence and never launches the verifier. `ALLOW` still authorizes only `repository-audit.v1`; it is not release, patch, retry or shell-command authority.

Local adversarial tests cover subject policy shadowing, scope elevation, workflow-ref substitution, policy tampering, repository spoofing and overlapping checkouts. Hosted proof at reusable-workflow SHA `1103ac3978441253251a9a818a4977fbdbdb350a` passed in run `34707376819` and again with the caller at `main` `4ebd5df` in run `34767472911`; Infrastructure CI run `34767472551` also passed. The proof now pins `4ebd5df21a9e71d4b19ecfd9e48cfaab79293b67`; `trusted-repository-audit.yml` is byte-identical between the two SHAs, so the proven workflow bytes are unchanged, but the hosted run for the new ref is still pending. The proof covers this workflow and checked-in policy only: a consumer must adopt its own pinned reference and pass its own compatibility run.

GitHub.com documents `job.workflow_repository`, `job.workflow_ref` and `job.workflow_sha` for reusable-workflow identity. Actionlint 1.7.12 predates those fields, so `.github/actionlint.yaml` suppresses only its exact unknown-property diagnostic for this workflow; all other lint checks remain active.
