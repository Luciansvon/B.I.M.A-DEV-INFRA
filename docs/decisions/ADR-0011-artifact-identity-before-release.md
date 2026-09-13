# ADR-0011 — Artifact identity before release automation

Status: **Accepted.**
Date: 2026-09-13.
Decision owner: Bima; Solo implementation.

## Context

The architecture requires build-once and same-artifact verification, but the
repository had no executable contract that binds final artifact bytes to a
subject and policy. Adding a generic build or release executor would expand the
trust boundary before a real consumer exists. Exact hashing and later
re-verification are deterministic and useful without that expansion.

## Decision

1. Add strict, provider-neutral request, manifest, and verification contracts.
2. Hash only declared regular files under a declared root; reject unsafe paths,
   symlinks, oversized files, missing files, and concurrent mutation.
3. Bind manifests to project, repository subject, policy, request digest,
   artifact role, ownership, sensitivity, retention metadata, size, and SHA-256.
4. Make any missing, changed, or unsafe artifact a fail-closed verification
   result. Preserve every unresolved artifact.
5. Keep building, testing behavior, signing, attestation, upload, release, and
   consumer adoption outside this increment.

## Alternatives considered

| Alternative | Decision |
|---|---|
| Generic project build/release runner | Rejected until command isolation and a real consumer justify it. |
| Hash only the primary binary | Rejected; checksums, SBOMs, signatures, attestations, and reports also need explicit identity. |
| Trust filenames or CI artifact names | Rejected; names do not prove byte identity. |
| Make GitHub attestation mandatory now | Deferred; attestation is separate provenance evidence and requires a publication context. |

## Consequences

DEV-INFRA can now prove that a declared local artifact set did or did not change
between bounded stages. It still cannot claim that an application was built,
behaved correctly, was signed correctly, or was released. Consumers remain
opt-in. The final byte-changing step must precede manifest creation.

## Evidence

- [Artifact Identity Contract](../standards/ARTIFACT-IDENTITY.md)
- Local and hosted validation are recorded in the implementation audit.

## Supersedes / Superseded by

Extends ADR-0009's same-artifact rule and ADR-0010's deterministic-first
delivery order. It does not supersede existing evidence or release decisions.
