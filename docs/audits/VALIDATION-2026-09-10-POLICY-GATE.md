# Policy Gate v1 local validation

Date: 2026-09-10

Scope: first executable project/policy/request/decision contract and bounded `repository-audit.v1` integration.

Merged revision: `60ec750974f922805ef418a5adef3f992603f8e3` through PR #19.

## Result

Status: **LOCAL AND HOSTED DEV-INFRA PASS; REAL-CONSUMER COMPATIBILITY PENDING.**

The implementation validates exact v1 JSON contracts, binds a request to exact trusted policy bytes, denies unapproved resource scope, and launches only the reviewed repository audit after revision, clean-worktree, output-containment and timeout checks. This result does not prove an OS sandbox, arbitrary project-command safety, application correctness or consumer compatibility.

## Evidence

| Check | Result |
|---|---|
| Policy Gate focused unit tests | 14 passed |
| Full Python regression suite | 49 passed, 1 skipped, 0 failed |
| Windows symlink test | Skipped because the current account lacks WinError 1314 symlink privilege; hosted Windows remains required |
| Positive fixture | `ALLOW`, request digest and policy SHA-256 retained |
| Network/credential elevation fixture | `DENY`, `RESOURCE_SCOPE_DENIED`; operation not launched |
| Modified subject policy with prior trusted hash | `DENY`, `UNTRUSTED_POLICY_HASH` |
| Wrong revision / dirty worktree | `DENY`, operation not launched |
| Existing repository-audit integration | Allowed clean temporary Git repository produced `decision.json`, `audit/result.json` and `audit/report.md` with audit status `pass` |
| Repository audit of the implementation tree | 83 files, 140 local links, 0 findings; correctly labeled dirty at base revision `f43814e` |
| Canonical v1 compatibility | `pass`; SHA-256 `1a833d98c010ab94aafcb5bb112117899d59541b4a9437f18285fc1a728f4d5a` |
| Agent packet pass behavior | `not-needed`; no pass-path packet |

## Hosted evidence

[Infrastructure CI run `34442172182`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34442172182) completed successfully after PR #19 merged. Downloaded artifacts were inspected independently:

| Evidence | Ubuntu 24.04 | Windows 2025 |
|---|---:|---:|
| Regression tests | 49 passed | 49 passed |
| Repository files / local links | 83 / 140 | 83 / 140 |
| Audit findings | 0 | 0 |
| Revision / dirty | `60ec750`, false | `60ec750`, false |
| Canonical SHA-256 | `c671edefe36c6d865b9b6099032f6f9ad82ac7c61faba21e87f9e577c5677afe` | identical |
| Agent packet | absent as required for pass | absent as required for pass |

Workflow-lint evidence reports `actionlint` and pre-flight status `pass`. This proves the merged DEV-INFRA increment on both hosted operating systems; it does not prove a consuming project's compatibility.

Commands:

```text
python -I -m unittest discover -s tests -p test_policy_gate.py -v
python -I -m unittest discover -s tests -v
python -I automation/repository_audit.py --root . --policy .bima/audit.json --output .artifacts/policy-gate-validation/audit
python -I automation/canonical_evidence.py --input .artifacts/policy-gate-validation/audit/result.json --output .artifacts/policy-gate-validation/evidence
python -I automation/agent_packet.py --input .artifacts/policy-gate-validation/evidence/canonical.json --output .artifacts/policy-gate-validation/agent
```

The local repository audit recorded the then-committed base revision and `dirty=true`, so it remains labeled local implementation evidence. The hosted artifacts above provide reviewed-commit proof for DEV-INFRA. Do not change the fixture or AI-COLOR-COMPARE consumer pins until a separate real-consumer compatibility run passes.

## Repository governance observed

The GitHub branch-protection API was inspected after PR #18 merged. `main` requires the actual `Workflow lint`, `Repository audit (ubuntu-24.04)` and `Repository audit (windows-2025)` checks with strict update. Admin enforcement, linear history and conversation resolution are enabled; approving review count is `0`; force-push and deletion are disabled. Repository rulesets remain empty because this repository uses classic branch protection. License selection remains an owner decision.

## Remaining boundary

- No real-consumer Policy Gate compatibility run exists yet.
- The trusted wrapper must provide policy bytes/hash, actor and validity window independently of subject-controlled content.
- The local developer shell is not an isolation boundary and inherited OS/network capabilities are not removed by this Python module.
- Only `repository-audit.v1` is supported; unknown commands and providers deny.
- `HUMAN_REQUIRED` is reserved by schema but no privileged operation class is implemented.
- Existing v1 evidence and agent-packet formats are unchanged.
