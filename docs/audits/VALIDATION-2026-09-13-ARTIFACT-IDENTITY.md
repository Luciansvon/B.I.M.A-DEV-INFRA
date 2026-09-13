# Artifact Identity v1 validation — 2026-09-13

Status: **LOCAL PASS / HOSTED PENDING**

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
- Local Task/actionlint binaries are unavailable. Workflow validation and
  whitespace review remain pending hosted CI/review; they are not reported as
  local passes.

## Hosted evidence

Pending pull-request Ubuntu/Windows artifacts. A green workflow status alone is
not sufficient; inspect manifest and verification bytes before changing this
status.

The first Ubuntu PR attempt exposed a pre-existing cleanup flake in the trusted
launcher test fixture: assertions completed, then temporary `.git` removal saw
the directory change concurrently. The bounded rerun passed. The fixture now
disables Git automatic GC and maintenance before committing; final hosted proof
must come from a new commit, not the successful rerun alone.

## Boundaries

This increment proves byte identity for declared local files. It does not prove
build provenance, runtime/GUI behavior, signing, attestation, upload, remote
retention, or release readiness.
