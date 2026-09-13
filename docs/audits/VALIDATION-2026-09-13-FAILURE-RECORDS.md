# Failure-record activation validation — 2026-09-13

## Verdict

Five real shared-infrastructure cases are represented as canonical, public,
`ACTIVE` `bima-failure-record.v1` records. Bima approved all five as the
independent reviewer in the [PR #27 review record]. `codex-curation` owns the
record transcription; `Luciansvon` is the distinct human reviewer.

Production Failure Memory remains correctly blocked at `5/100` records and
`0/10` held-out queries. No SQLite database was created.

[PR #27 review record]: https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/pull/27#issuecomment-5647770201

## Source

- Starting `main`: `633d6e6d1a59789f01d0fafb57af649a659ef3f1`.
- Candidate audit: [FAILURE-MEMORY-HISTORY-AUDIT-2026-09-13](FAILURE-MEMORY-HISTORY-AUDIT-2026-09-13.md).
- Record set: `failure-records/records.json`.
- Dataset: `dev-infra-reviewed-failures`.
- Canonical record-set SHA-256: `c61c37e0e226971c476e8c9f15d3a94ae93ac3adccbae6bf343ed428f5b505ac`.

## Signature derivation

Each signature is SHA-256 over the listed UTF-8 text with no trailing newline.
The input is bounded to stable tool, rule, location and diagnostic identity;
timestamps and run IDs remain evidence references rather than signature bytes.

| Record ID | Signature material | SHA-256 |
|---|---|---|
| `devinfra-action-reference-linter-compat-20260910` | `zizmor\|1.30.0\|self-repository\|.github/workflows/ci.yml:126:15\|uses=./.github/actions/normalize-rust-libtest` | `a98b7cfdb9e3db1108d12ad3a603af6d5c31728372ac777d5da5c658fdf7d07b` |
| `devinfra-dependabot-cooldown-20260909` | `zizmor\|1.30.0\|dependabot-cooldown\|.github/dependabot.yml\|exit=13` | `02e5862e89f166dcdc1d4df89161d4314455ab6fbdec51c2f252f72108085873` |
| `devinfra-pinact-version-comment-20260912` | `pinact\|4.1.1\|SHA-pinned action requires a version comment for verifiability\|.github/workflows/trusted-launcher-proof.yml:17` | `aade4b32d65876fa1bf9e1fe92f83fcc0499478de0d0dda4bddfa478544a62b6` |
| `devinfra-posix-network-path-20260912` | `python\|3.13.15\|test_database_rejects_repository_sync_and_network_locations\|PermissionError:[Errno 13] Permission denied:'/server'\|ubuntu-24.04` | `fc811bd75d49a2ef94357a2c3bfbcf41aba50230abb908ab4472739410550853` |
| `devinfra-trust-bundle-id-drift-20260912` | `trusted-launcher\|TRUST_FILE_MISSING\|bundle=dev-infra-repository-audit-v1\|verifier_launched=false` | `56e456f7a9fcc93e66089dacf1fb1523860d554b5da15eaac08cbf6655ba3778` |

## Local evidence

- Failure-record validation: `PASS`; total `5`, real verified `5`, synthetic `0`.
- Failure-memory production gate: `BLOCKED`, `INSUFFICIENT_REAL_CASES`,
  `5/100`; target database absent.
- Production benchmark gate after binding the query request to the new record
  digest: `BLOCKED`, `INSUFFICIENT_REAL_CASES`, query count `0`, metrics `null`;
  target database absent.
- Full regression: `111` passed, `1` skipped, `0` failed in `65.325` seconds.
  The skip is the existing Windows symlink-privilege boundary.
- Repository audit: `PASS`; `146` files checked and `0` findings.

## Boundary

These five records improve the reviewed corpus but do not activate retrieval.
Do not create or populate production SQLite/FTS files before `100` real active
records and `10` genuinely held-out queries exist. Synthetic queries or copied
diagnostics must not be used to satisfy the held-out gate.

## First hosted attempt

PR #28 run `34730811769` correctly parsed and gated all five records, but the
Ubuntu and Windows P3-P5 assertion still expected the former production count
of zero. The assertion is updated to the reviewed count of five; replacement
hosted evidence passed. This new shared-workflow failure is not silently added
as a sixth active record because it has not received independent review.

## Replacement hosted evidence

- Infrastructure CI run `34730928028`: workflow lint, Ubuntu 24.04 and Windows
  2025 passed at the corrected revision.
- Both operating systems ran all `111` tests and emitted canonical record files
  with SHA-256 `c61c37e0e226971c476e8c9f15d3a94ae93ac3adccbae6bf343ed428f5b505ac`.
- Both record summaries report `5` real active records. Both memory reports are
  `BLOCKED: INSUFFICIENT_REAL_CASES`, `database_created=false`.
- Both benchmark reports are `BLOCKED: INSUFFICIENT_REAL_CASES`, query count
  `0`, metrics `null`, `database_created=false`.
- Both repository audits passed with `146` files and zero findings.
- Trusted launcher run `34730928155`: launcher and Policy Gate returned `ALLOW`,
  reason `MATCHED_REPOSITORY_AUDIT_RULE`, and `verifier_launched=true`.
