# Canonical evidence validation — 2026-09-09

## Verdict

Local Windows and initial GitHub-hosted validation passed. The final merge revision still requires its own `main` run before this increment is described as complete.

## Source

- Base revision: `a180c0633a9e48d289297eb8aae29e474160e62a`.
- Branch: `codex/cost-aware-p0-canonical-evidence`.
- Initial source commit: `acc08409b70df338db02da8d2c563fd7c21650c9`.
- Pull request: [#11](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/pull/11).
- Initial hosted run: [34319510404](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34319510404).

## Local Windows evidence

- Eight new canonical-evidence regression tests passed: volatile timestamp/order/line-ending normalization, finding ordering, malformed contract rejection, duplicate/non-finite JSON rejection, exact hash verification, metadata separation, failed-result preservation, and sanitized CLI failure/stale-output cleanup.
- A local repository audit and canonicalization produced all three evidence files. The generated checksum matched an independent SHA-256 of `canonical.json`.
- Local evidence correctly records a dirty subject at base revision `a180c0633a9e48d289297eb8aae29e474160e62a`; it is not used as proof of clean cross-platform equivalence.
- `task verify`: pass; 27 tests ran, 26 passed, and the real-symlink test skipped because this Windows session lacks symlink privilege.
- Repository audit: pass; 57 files and 58 local links checked, policy SHA-256 `881ca66013decc632570b2c37752606a3cbf734d18a39666d2fcbd9387b93c11`, and zero findings.
- Local dirty canonical SHA-256 was `3dfc95f793d8cf9328d3904d364dc6cbf9b298686571f672776968be7268a90b`; the checksum file and an independent file hash matched.
- Pre-flight, actionlint v1.7.12, and both Git diff whitespace checks passed.

## Initial GitHub-hosted evidence

- Ubuntu 24.04 and Windows 2025 each ran all 27 regression tests with no skips or failures.
- Both audit artifacts report `status=pass`, 57 files checked, 58 local links checked, policy SHA-256 `881ca66013decc632570b2c37752606a3cbf734d18a39666d2fcbd9387b93c11`, and zero findings.
- The two `canonical.json` files are byte-identical. Their files, declared checksum files, and independent hashes all match SHA-256 `4eef8f0edcf46086c5f6385adef4956c83cf54e48f6abcfade6d5323ca6c6513`.
- Execution metadata remains deliberately distinct: Linux reports `x86_64`, Windows reports `AMD64`, and their source timestamps/raw SHA-256 values differ while both reference the same canonical hash.
- The pull-request audit revision is GitHub's synthetic merge commit `8a0d571d788d6795fc4dae7c5ae0fc196960a9cb`; run metadata identifies source commit `acc08409b70df338db02da8d2c563fd7c21650c9`.
- Workflow/pre-flight and actionlint checks passed; retained evidence confirms zizmor, pinact, and action-validator still execute successfully.

## Boundary

The current adapter accepts repository-audit result version 1 only. The deterministic serializer is intentionally narrower than RFC 8785 and rejects floating-point/non-finite inputs. It is not an attestation, signature, trusted-runner proof, release provenance claim, build reproducibility claim, agent packet, or universal adapter for unimplemented modules.
