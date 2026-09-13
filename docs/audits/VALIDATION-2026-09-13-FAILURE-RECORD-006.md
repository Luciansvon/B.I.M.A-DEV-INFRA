# Sixth failure-record activation validation — 2026-09-13

## Verdict

The stale hosted corpus-count assertion is a real, public,
shared-infrastructure failure/fix case. Bima approved it as the independent
reviewer in the [PR #28 review record]. `codex-curation` owns the canonical
transcription; `Luciansvon` is the distinct reviewer.

The portable corpus is `6/100`. Production Failure Memory and its benchmark
remain correctly blocked with `0/10` held-out queries. No SQLite database is
created.

[PR #28 review record]: https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/pull/28#issuecomment-5650572173

## Failure, cause, and fix

- Failure run [`34730811769`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34730811769) parsed five valid real records on Ubuntu and Windows, then raised `AssertionError` because the P3-P5 workflow assertion still expected zero.
- Cause/fix commit [`025857dce68d4026f9d3c3060ec6421582b45f0d`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/commit/025857dce68d4026f9d3c3060ec6421582b45f0d) changed the stale expected count from zero to five.
- Replacement run [`34730928028`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34730928028) passed on Ubuntu, Windows, and workflow lint. Trusted launcher run [`34730928155`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34730928155) also passed.

## Canonical record

- ID: `devinfra-failure-count-assertion-drift-20260913`.
- Reason: `FAILURE_CORPUS_COUNT_ASSERTION_DRIFT`.
- Scope: `global`, promoted because the root cause belongs to shared infrastructure.
- Review: `codex-curation` owner; `Luciansvon` reviewer; reviewed at `2026-09-13T03:07:27Z`.
- Signature material, UTF-8 without trailing newline:
  `github-actions|Verify P3-P5 gated core contracts|assert real_verified_records==0|actual=5|AssertionError`.
- Signature SHA-256:
  `362530a0d75b75d651abc201ffa8bdca6e22f1f8accc41b3eb96f316f73d8d86`.
- Canonical six-record set SHA-256:
  `756f513008b11b84db153dde1c575449f88f61b422ac83fdd66860217d8e24b6`.

## Activation boundary

This record raises only the reviewed corpus count. It does not create a
held-out query, activate SQLite/FTS5 retrieval, authorize retries, or change a
consumer. The `100` real-case and `10` genuinely held-out-query gates remain
unchanged.

## Validation

### Local evidence

- Failure-record validation: `PASS`; total `6`, real verified `6`, synthetic
  `0`.
- Canonical six-record set SHA-256:
  `756f513008b11b84db153dde1c575449f88f61b422ac83fdd66860217d8e24b6`.
- Failure-memory production gate: `BLOCKED`,
  `INSUFFICIENT_REAL_CASES`, `6/100`; target database absent.
- Production benchmark gate: `BLOCKED`, `INSUFFICIENT_REAL_CASES`, query
  count `0`; target database absent.
- Full regression: `111` tests, `1` skipped, `0` failed in `55.573`
  seconds. The skip is the existing Windows symlink-privilege boundary.
- Repository audit: `PASS`; `149` files checked and `0` findings.
- `git diff --check`: `PASS`.

### Hosted evidence

- PR #30 Infrastructure CI run [`34752079512`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34752079512): workflow lint, Ubuntu 24.04, and Windows 2025 passed at revision `71cedaf05731fa80e67f7d377deea1c8ede35ab3`.
- Both operating systems ran all `111` tests and emitted six real records with
  canonical SHA-256
  `756f513008b11b84db153dde1c575449f88f61b422ac83fdd66860217d8e24b6`.
- Inspected Ubuntu and Windows artifacts report Failure Memory and benchmark
  `BLOCKED: INSUFFICIENT_REAL_CASES`, query count `0`, and
  `database_created=false`.
- Both repository-audit artifacts report `PASS`, `149` files, `171` local
  links, and zero findings.
- PR #30 trusted launcher run [`34752079705`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34752079705): decision `ALLOW`, reason
  `MATCHED_REPOSITORY_AUDIT_RULE`, and `verifier_launched=true`.
