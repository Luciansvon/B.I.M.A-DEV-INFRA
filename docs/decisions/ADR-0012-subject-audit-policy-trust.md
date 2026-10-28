# ADR-0012 - Subject audit-policy trust boundary

Status: Accepted.
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

Open questions resolved by implementation: the base commit is the
GitHub-provided `pull_request.base.sha`, never a `workflow_call` input; `push`,
`schedule` and `workflow_dispatch` keep using the checked-out policy; the
reusable workflow passes the event identity through environment variables set
from the GitHub event, not through caller-controlled inputs.

## Implementation

The reusable workflow checks out the subject with full history, then passes
`github.event_name` and `github.event.pull_request.base.sha` as environment
identity. On `pull_request`, the launcher verifies the base commit exists and is
an ancestor of the subject, validates the base project declaration, refuses a
changed `audit_policy` path, and materializes the base policy bytes outside both
checkouts. The repository audit reads those exact bytes, so the head policy is
never consulted. Missing or malformed base artifacts deny before the verifier.

## Evidence

- `automation/trusted_policy_launcher.py:_base_audit_policy`
- `automation/trusted_policy_launcher.py:launch`
- `automation/repository_audit.py:load_policy`
- `automation/policy_gate.py:execute_repository_audit`
- `.github/workflows/trusted-repository-audit.yml`
- `.bima/project.json`
- `policies/trust-bundles/dev-infra-repository-audit.v1.json`
- `tests/test_trusted_policy_launcher.py`
- `tests/test_repository_audit.py`
- External Final Audit Ledger, `SEC-HIGH-01`, 2026-10-28.

## Supersedes / Superseded by

None.
