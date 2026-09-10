# Policy Gate v1 local validation

Date: 2026-09-10

Scope: first executable project/policy/request/decision contract and bounded `repository-audit.v1` integration.

Branch: `codex/policy-contract-v1`, based on merged `main` at `f43814e9ab3d25015767db48b2885ab7fab3f5ea`.

## Result

Status: **LOCAL PASS; HOSTED EVIDENCE PENDING.**

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

Commands:

```text
python -I -m unittest discover -s tests -p test_policy_gate.py -v
python -I -m unittest discover -s tests -v
python -I automation/repository_audit.py --root . --policy .bima/audit.json --output .artifacts/policy-gate-validation/audit
python -I automation/canonical_evidence.py --input .artifacts/policy-gate-validation/audit/result.json --output .artifacts/policy-gate-validation/evidence
python -I automation/agent_packet.py --input .artifacts/policy-gate-validation/evidence/canonical.json --output .artifacts/policy-gate-validation/agent
```

The repository audit records the committed base revision and `dirty=true`, so it is local implementation evidence rather than hosted reviewed-commit proof. GitHub Actions remains the authoritative publication path; do not change the fixture or AI-COLOR-COMPARE consumer pins until the branch is reviewed and both hosted operating-system jobs pass.

## Repository governance observed

The GitHub branch-protection API was inspected after PR #18 merged. `main` requires the actual `Workflow lint`, `Repository audit (ubuntu-24.04)` and `Repository audit (windows-2025)` checks with strict update. Admin enforcement, linear history and conversation resolution are enabled; approving review count is `0`; force-push and deletion are disabled. Repository rulesets remain empty because this repository uses classic branch protection. License selection remains an owner decision.

## Remaining boundary

- No hosted run exists for this increment yet.
- The trusted wrapper must provide policy bytes/hash, actor and validity window independently of subject-controlled content.
- The local developer shell is not an isolation boundary and inherited OS/network capabilities are not removed by this Python module.
- Only `repository-audit.v1` is supported; unknown commands and providers deny.
- `HUMAN_REQUIRED` is reserved by schema but no privileged operation class is implemented.
- Existing v1 evidence and agent-packet formats are unchanged.
