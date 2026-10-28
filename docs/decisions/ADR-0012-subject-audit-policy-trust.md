# ADR-0012 - Subject audit-policy trust boundary

Status: Proposed.
Date: 2026-10-28.
Decision owner: Bima.

## Context

`trusted_policy_launcher.py` reads `.bima/project.json` from the subject
checkout, and `policy_gate.py` passes its `audit_policy` value to
`repository_audit.py`. The trust bundle pins only
`policies/repository-audit/dev-infra.v1.json`; it does not bind
`.bima/audit.json`. A pull request can therefore remove required files or raise
`max_file_bytes` in the audit policy and still satisfy the required
`Trusted repository audit proof / audit` context.

The existing adversarial test covers shadowing the trusted policy path, not
changing the subject audit policy. `docs/standards/SECURITY-BASELINE.md` already
warns that policy or ignore changes can weaken a check, and `main` currently
requires zero approvals. The gap is documented but not decided.

## Decision

Treat the subject audit policy as reviewable subject configuration, not as
trusted policy bytes. For pull-request audit runs, evaluate `.bima/audit.json`
from the pull request's base commit rather than from the PR head. For push,
schedule, and manual runs, use the checked-out subject policy.

Do not add a subject-policy hash to the trust bundle in this iteration. The
trusted infrastructure checkout is pinned to the caller's base SHA, so a bundle
hash would make a legitimate policy change unmergeable without a separate
infrastructure release.

## Alternatives considered

1. Hash-pin `.bima/audit.json` in
   `policies/trust-bundles/dev-infra-repository-audit.v1.json`. Rejected for
   now: the bundle is read from the base commit, so a PR cannot update the pin
   and the policy in the same change.
2. Move every project's audit policy into DEV-INFRA. Rejected: required files
   and size limits are project-owned data, not shared infrastructure.
3. Accept subject-owned policy and rename the check so it no longer claims
   trust. Rejected: the check is already a required merge context and the name
   is part of the public contract.
4. Evaluate the policy from the base commit. Proposed.

## Consequences

Positive: a PR cannot weaken the audit that evaluates it; no new
cross-repository policy; the trusted code boundary is unchanged.

Negative: the launcher must establish the base commit without trusting an
arbitrary workflow input; shallow checkouts and merge commits need explicit
handling; policy changes require a separate merged PR before they take effect;
tests and documentation must cover the new path.

Open questions: derive the base commit from the pull-request event or from the
merge commit's first parent; decide behavior for `push` and `workflow_dispatch`;
confirm the reusable workflow can pass the base identity without adding a
spoofable input.

## Evidence

- `automation/trusted_policy_launcher.py:201-205`
- `automation/policy_gate.py:366-372`
- `.bima/project.json:12`
- `policies/trust-bundles/dev-infra-repository-audit.v1.json:6-7`
- `tests/test_trusted_policy_launcher.py:90-105`
- `docs/standards/SECURITY-BASELINE.md:27`
- External Final Audit Ledger, `SEC-HIGH-01`, 2026-10-28.

## Supersedes / Superseded by

None.
