# Result normalization action local validation

Date: 2026-09-10

Status: **LOCAL PASS; HOSTED ACTION AND CONSUMER PROOF PENDING.**

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

The composite action is also invoked from the DEV-INFRA Linux/Windows CI matrix. Hosted artifacts and action metadata validation remain pending until the pull request executes.

## Boundary

The action consumes native evidence only. It does not execute Cargo, authorize an operation, retry, repair, publish or change consumer pins. The real AI-COLOR-COMPARE opt-in must retain the independent v1 audit path and prove rollback after this action is merged at a reviewed SHA.
