# P0-P5 local validation

Date: 2026-09-12; local verification refreshed 2026-09-13

Status: **LOCAL CONTRACT PASS; HOSTED LAUNCHER PROOF PENDING; DATA-GATED ACTIVATION BLOCKED.**

Baseline inspected before changes and re-fetched after implementation: local `HEAD` and `origin/main` both `d748b66e63fa40c311bba5d1efd22d1999560e20`, divergence `0/0`, with no open pull request. Main protection and repository-level Action SHA enforcement are active. AI-COLOR migration is closed without a consumer change.

## Implemented

| Priority | Result | Activation state |
|---|---|---|
| P0 | Roadmap/current-state sync and evidence correction | Complete locally |
| P1 | Trusted reusable repository-audit launcher and adversarial fixtures | Local pass; hosted workflow proof pending |
| P2 | DEV-INFRA action evidence inspected from run `34470140936` | Complete; consumer migration closed unchanged |
| P3 | Portable reviewed failure-record contract | Complete; production record set remains empty |
| P4 | Rebuildable SQLite/FTS5 plus held-out retrieval benchmark and hard corpus/query gates | Mechanics pass; production activation `BLOCKED` at `0/100` and `0/10` |
| P5 | Deterministic cross-project experiment-readiness gate | Gate pass; no provider active |

## Local evidence

- Trusted launcher focused suite: 7 passed, 0 failed.
- Failure-record focused suite: 7 passed, 0 failed.
- Failure-memory focused suite: 7 passed, 0 failed after correcting restricted-record access and proving inactive real records cannot satisfy the corpus gate.
- Failure-memory benchmark focused suite: 7 passed, 0 failed; exact retrieval reached 1,000,000 ppm recall/MRR with zero false/stale hits on synthetic mechanics fixtures.
- Experiment gate focused suite: 8 passed, 0 failed.
- Full regression: 111 passed, 1 skipped, 0 failed in 75.858 seconds. The skip is Windows symlink creation privilege and does not bypass a product assertion.
- Repository audit after license selection and proof caller addition: 144 files, 160 supported local links, zero findings.
- Actionlint 1.7.12: zero findings after a path-scoped compatibility suppression for GitHub.com's newer `job.workflow_*` fields.
- Prek built-in safety hooks, pinact 4.1.1 and zizmor 1.30.0: pass; zizmor reported zero findings.
- Eight representative request/decision/report documents validated against their JSON Schemas.

The hosted normalization artifacts for run `34470140936` report 75 tests passed on both Ubuntu 24.04 and Windows 2025. Both normalized results are `PASS`, reason `ALL_EXPECTED_TESTS_PASSED`, with `29/29` observed/expected tests and matching source/policy hashes.

## Remaining proof boundaries

- The new reusable launcher workflow has not run on GitHub from this branch.
- The existing CI matrix now emits separate P3-P5 record-summary, memory-readiness, retrieval-benchmark and experiment-decision artifacts; hosted execution remains pending until the branch is pushed.
- Production failure memory must not be created until 100 real reviewed cases exist.
- No optional experiment becomes executable until demand exists in at least two projects and a separate Policy Gate authorizes it.
- Apache-2.0 is selected and its local bytes match GitHub's canonical license template; hosted license detection remains pending publication.
