# Result normalization action local validation

Date: 2026-09-10

Status: **DEV-INFRA HOSTED ACTION PASS; CONSUMER MIGRATION CLOSED WITHOUT CHANGE.**

## Evidence

Focused result-normalizer regression: 15 passed, 0 failed.

Full regression: 75 passed, 1 skipped, 0 failed. The skipped local Windows symlink case requires a privilege unavailable to the current account and is unrelated to normalization.

Repository audit: 105 files, 149 supported local links, zero findings. Canonical v1 audit evidence remained `pass`, SHA-256 `931b5c33d4d3d7f1b048063af16c4cda99cef6ff8f477a6225dea6a72dea5382`; the implementation tree was correctly marked dirty at revision `ce636f6213a6d6d04fe9b1bfa21e86d948c60425`.

New coverage proves:

- strict project config produces a runtime-bound normalization request;
- command and canonical config policy digests are deterministic;
- subject revision, cleanliness, attempt, native exit and source hashes come from runtime inputs;
- incomplete config-mode identity fails closed;
- legacy direct-request CLI behavior remains covered and unchanged.

The composite action was invoked from the DEV-INFRA CI matrix in run `34470140936` at revision `d748b66e63fa40c311bba5d1efd22d1999560e20`:

- Ubuntu 24.04: 75 tests passed; normalized verdict `PASS`, reason `ALL_EXPECTED_TESTS_PASSED`, observed/expected `29/29`.
- Windows 2025: 75 tests passed; normalized verdict `PASS`, reason `ALL_EXPECTED_TESTS_PASSED`, observed/expected `29/29`.
- Both artifacts retained the same source SHA-256 and policy SHA-256. Attempt IDs remain OS-specific as designed.

## Boundary

The action consumes native evidence only. It does not execute Cargo, authorize an operation, retry, repair, publish or change consumer pins. AI-COLOR-COMPARE migration was explicitly closed without a change; the independent v1 path remains active.
