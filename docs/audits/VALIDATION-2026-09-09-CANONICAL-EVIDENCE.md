# Canonical evidence validation — 2026-09-09

## Verdict

Local Windows validation passed. Hosted evidence is pending and must pass before this increment is merged or described as fully validated.

## Source

- Base revision: `a180c0633a9e48d289297eb8aae29e474160e62a`.
- Branch: `codex/cost-aware-p0-canonical-evidence`.
- Pull request and hosted run: pending.

## Local Windows evidence

- Eight new canonical-evidence regression tests passed: volatile timestamp/order/line-ending normalization, finding ordering, malformed contract rejection, duplicate/non-finite JSON rejection, exact hash verification, metadata separation, failed-result preservation, and sanitized CLI failure/stale-output cleanup.
- A local repository audit and canonicalization produced all three evidence files. The generated checksum matched an independent SHA-256 of `canonical.json`.
- Local evidence correctly records a dirty subject at base revision `a180c0633a9e48d289297eb8aae29e474160e62a`; it is not used as proof of clean cross-platform equivalence.
- `task verify`: pass; 27 tests ran, 26 passed, and the real-symlink test skipped because this Windows session lacks symlink privilege.
- Repository audit: pass; 57 files and 58 local links checked, policy SHA-256 `881ca66013decc632570b2c37752606a3cbf734d18a39666d2fcbd9387b93c11`, and zero findings.
- Local dirty canonical SHA-256 was `3dfc95f793d8cf9328d3904d364dc6cbf9b298686571f672776968be7268a90b`; the checksum file and an independent file hash matched.
- Pre-flight, actionlint v1.7.12, and both Git diff whitespace checks passed.

## Boundary

The current adapter accepts repository-audit result version 1 only. The deterministic serializer is intentionally narrower than RFC 8785 and rejects floating-point/non-finite inputs. It is not an attestation, signature, trusted-runner proof, release provenance claim, build reproducibility claim, agent packet, or universal adapter for unimplemented modules.
