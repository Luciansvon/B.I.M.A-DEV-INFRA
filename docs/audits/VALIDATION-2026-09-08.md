# Local validation record — 2026-09-08

Environment: Windows, Python 3.13.15, Git CLI, actionlint 1.7.12. Base commit: `f4d0d1538c6b7ecdc5c1c6cb1b32fa74c49fce14`; branch: `codex/infra-audit-foundation`; changes are local and uncommitted.

Pre-publication local regression run: **19 tests run, 18 passed, 1 skipped**, in 11.153 seconds. Both workflow files passed actionlint with exit 0. The completed repository hygiene run returned `pass` with zero findings; exact counters and hashes are in `result.json`. Remote `origin/main` was fetched/pruned again and remained at the audited base commit.

The first hosted pull-request run was [34225893583](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34225893583) at commit `9722c420202dafc0733fb536e9c46b1d2b9db625`. Ubuntu and Windows each ran all 19 tests with no skip, including the real symlink fixture; both audits passed with zero findings. Downloaded artifacts showed different validator and policy byte hashes between operating systems because Windows checkout converted LF to CRLF. That evidence led to `.gitattributes` LF enforcement. Final hosted results after the correction supersede this initial run and must be inspected before merge.

The corrected hosted pull-request run was [34226270454](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34226270454). Both operating systems again ran all 19 tests and passed with zero audit findings. Validator SHA-256 `4820e569910dbd41c5765e4d291a9e3600f2ebe67a4d93a017f0ba5a04e05805` and policy SHA-256 `6cc5dd19b28e341c110496b107cabd43ce27ac769013a820ddc6acb0326e9cf0` matched across platforms, proving the line-ending correction. The workflow-lint check passed, but its downloaded log was empty because actionlint is silent on success; the final follow-up writes tool version, pass status, and workflow count into that evidence artifact.

## Evidence paths and interpretation

| Check | Local evidence | Interpretation |
|---|---|---|
| Regression suite | `.artifacts/tests.log` | Actual unittest case outcomes, including any platform skip |
| Repository hygiene | `.artifacts/audit/result.json`, `.artifacts/audit/report.md` | Audit counters, findings, subject revision/dirty state, validator/policy hashes |
| Workflow syntax | `.artifacts/actionlint.log` | actionlint 1.7.12 for both workflow files; shellcheck/pyflakes explicitly disabled because unavailable locally |
| Patch whitespace | `.artifacts/diff-check.log` | Whitespace validation only, not functional proof |
| GitHub baseline | `.artifacts/github-baseline.json` | Read-only repository/Actions configuration snapshot |

The test suite exercises clean/missing/empty files, broken/unsafe/encoded links, fenced examples, ignored/untracked inputs, malformed/duplicate/non-finite/deep JSON, policy validation, file budgets, caller import isolation, escaped reports, and actual CLI exit/evidence behavior for pass/fail/error.

The real symlink fixture is skipped on this Windows session because the OS denies symlink creation (`WinError 1314`). It remains in the suite for hosted Linux. A skipped case is not a passing case.

The initial audit intentionally reported a missing validation-record link while the record was being authored; the final report must be regenerated after all documentation exists. No local output is treated as hosted CI, external-consumer, secrets-scan, or application-build proof.

An earlier test incorrectly assumed the local Python JSON decoder must reject a 2,000-level valid array. Python 3.13.15 accepted it. The fixture now checks that deep JSON never aborts the audit, allows runtime-specific parser depth limits, and separately verifies handling of a decoder `RecursionError`. The earlier failed test log is retained at `.artifacts/tests-initial-failure.log`; the final run above supersedes it.

## Verification tool provenance

actionlint was downloaded from the upstream `v1.7.12` release into ignored `.tools/`. Its Windows amd64 archive SHA-256 was checked against the GitHub release asset digest before execution:

```text
6e7241b51e6817ea6a047693d8e6fed13b31819c9a0dd6c5a726e1592d22f6e9
```

No package was added to the Python runtime or project dependency set. The GitHub-hosted workflows and Actions upload/setup steps have not been executed because publication was not requested.
