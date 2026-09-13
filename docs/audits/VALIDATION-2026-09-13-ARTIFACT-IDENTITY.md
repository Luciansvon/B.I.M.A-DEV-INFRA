# Artifact Identity v1 validation — 2026-09-13

Status: **LOCAL + HOSTED PASS / CONSUMER DEFERRED**

## Scope

- Additive request, manifest, and verification schemas.
- Deterministic create/verify CLI with no project command execution.
- Positive, changed, missing, unsafe-path, malformed-input, size-limit, and CLI
  exit-code coverage.
- CI fixture only; no consumer migration or release action.

## Local evidence

- Focused artifact-identity regression: 15 tests, 0 failures, 1 skipped
  Windows symlink case because the local account lacks symlink privilege.
- Full regression: 142 tests, 0 failures, 2 skipped Windows symlink cases.
- Draft 2020-12 schema syntax plus generated request/manifest/verification
  instances: valid for all three new schemas.
- Repository audit: 167 files, 188 local links, 0 findings.
- Python tabnanny, JSON parsing, and YAML syntax parsing: pass.
- Local Task/actionlint binaries are unavailable; their results below are
  hosted evidence, not local claims.

## Hosted evidence

PR #32 run `34767179664` passed workflow lint and the Ubuntu/Windows matrix at
head `e270d07e906390c96e3f2b4a9c3563f61ba8e6e1`. Downloaded artifacts were
inspected on both operating systems:

- 142 tests passed per OS;
- repository audit reported 167 files, 188 local links, and 0 findings;
- artifact verification returned `PASS`, `ALL_ARTIFACTS_MATCH`, matched `1/1`,
  and zero unresolved artifacts;
- request, manifest, verification, and audit bind the PR merge subject
  `f807f0863eb5416faecaa3b5ea7446d57e9c124a`;
- both OS artifacts share manifest SHA-256
  `49cbcaa2e38f17855c1b536662c3df17a9ccb09ee4a4482a0c9388a55de474da`;
- declared and downloaded fixture bytes share SHA-256
  `42678155dacb724fe82251b96b8276f5803eba17826101eaf5e26aac718f1f08`.

Trusted-launcher run `34767179786` separately returned `ALLOW`,
`MATCHED_REPOSITORY_AUDIT_RULE`, and `verifier_launched=true`. Artifact Identity
was not added to Policy Gate by this run.

The first Ubuntu PR attempt exposed a cleanup flake in the trusted
launcher test fixture: assertions completed, then temporary `.git` removal saw
the directory change concurrently. The bounded rerun passed. The fixture now
disables Git automatic GC and maintenance before committing. Run `34767179664`
is from the new commit and passed on the first attempt; the successful rerun of
the earlier commit is not used as acceptance evidence.

## Boundaries

This increment proves byte identity for declared local files. It does not prove
build provenance, runtime/GUI behavior, signing, attestation, upload, remote
retention, or release readiness.
