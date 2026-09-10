# Result normalizer v2 validation

Date: 2026-09-10

Scope: additive Rust libtest normalization plus bounded TypeScript diagnostic extraction.

Status: **LOCAL AND HOSTED REGRESSION PASS; REAL-CONSUMER MIGRATION PENDING.**

## Evidence

Focused command:

```text
python -I -m unittest discover -s tests -p test_result_normalizer.py -v
```

Result: 12 passed, 0 failed.

Full regression command:

```text
python -I -m unittest discover -s tests -v
```

Result: 61 passed, 1 skipped, 0 failed. The skipped Windows symlink test requires a privilege unavailable to the current account and is unrelated to result normalization.

Direct CLI fixture result: `PASS`, reason `ALL_EXPECTED_TESTS_PASSED`, zero diagnostics. Deterministic `result.json` SHA-256: `64db768920750ba0d53f388149aa78bfa95c84bbe39795129d43b8a51a7d501e`.

Repository audit of the implementation tree: 92 files, 143 supported local links, zero findings. Canonical audit evidence remained v1 `pass`, SHA-256 `f7a663ca39b696fabd9b786c978eb2ba6b754e8d990f25b92e19ea74054240e4`; the tree was correctly labeled dirty at the prior committed revision.

Hosted post-merge command path: `task test`, `task audit`, canonicalization and bounded packet generation in Infrastructure CI run [`34444750180`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34444750180) at revision `828ae9000dee8ce28f9c26c81efda34f34c1240b`.

Hosted artifact inspection:

- Ubuntu 24.04: 61 tests passed; repository audit passed with 92 files, 143 local links and zero findings;
- Windows 2025: 61 tests passed, including the symlink rejection test skipped by the unprivileged local Windows account; repository audit passed with the same counts and zero findings;
- canonical evidence SHA-256 matched across both systems: `b59f01ce717346072d329c998434fbb1106cff194d28f2b315bd947b5dcb321f`;
- both PASS artifacts contained zero agent packet files;
- workflow lint passed for two workflow files; prek, action-validator, pinact and zizmor passed, with one declared zizmor suppression.

Covered behavior:

- AI-COLOR-COMPARE success fixture retains three suite summaries and totals 29 observed passes;
- expected-count mismatch, missing summary, nonzero exit without test failure and exit/summary disagreement return `UNKNOWN`;
- a nonzero attempt with a reported failed test returns `FAIL`;
- command, policy, subject, environment and attempt identities are preserved;
- native sources are represented by SHA-256 and byte size, not raw text;
- source substitution or attaching an undeclared failure log is rejected before parsing;
- TypeScript diagnostic formatting is tested independently: records are repository-relative, capped at 50 records and 240 characters, and common credential shapes are redacted;
- the real TypeScript failure fixture is not attached to the Rust PASS result because its revision and command differ;
- malformed/duplicate/oversized inputs are rejected;
- canonical output is deterministic;
- isolated Python CLI writes `result.json` and preserves the PASS exit code.

## Evidence boundary

The successful and failed source runs are real AI-COLOR-COMPARE history, but the committed fixtures are bounded and sanitized reproductions. Hosted cross-platform regression is proven for DEV-INFRA itself; it does not prove current consumer opt-in, a hosted consumer FAIL result, retry equivalence, flakiness classification or v1-to-v2 rollback. Existing v1 consumers remain unchanged.
