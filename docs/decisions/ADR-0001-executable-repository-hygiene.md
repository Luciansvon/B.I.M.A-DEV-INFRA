# ADR-0001 — First executable repository hygiene module

Status: Accepted for local implementation; hosted validation and publication pending.
Date: 2026-09-08

## Context

At `f4d0d1538c6b7ecdc5c1c6cb1b32fa74c49fce14`, shared contracts and research existed but no executable workflows or tests existed. The existing architecture already separates caller configuration, shared implementation, and evidence. This change implements that design without selecting a new integration architecture or application framework.

## Decision

Start with an experimental offline repository hygiene script, explicit JSON policy, reusable workflow, and failure regression tests. Use Python standard library to avoid a new package dependency. Read the caller checkout as data and execute a separately pinned infrastructure checkout. Keep result version 1 specific to the audit module until additional module requirements exist.

The repo's CI runs the current checkout directly to test infrastructure changes before publishing a consumable SHA. Other projects supply input/policy only. Introduce a security baseline and retain machine-readable and human-readable evidence for failed as well as successful checks.

## Alternatives considered

- Implement every roadmap module: insufficient project/runner-specific evidence and much larger review surface.
- Documentation-only additions: would leave the confirmed lack of executable validation unresolved.
- Third-party Markdown/package stack: broader parsing but adds installation and maintenance; keep the initial syntax scope explicit instead.
- Use caller SHA/context to retrieve shared implementation: identifies the caller and can select wrong code. Require a separate full infrastructure SHA paired with the workflow pin.

## Consequences

The first module is useful for software, research, and documentation repositories. Markdown checks are partial and cannot be advertised as full link/security validation. Consumers maintain two matching SHA references. A clean hygiene result is not an application, supply-chain, or release verdict. Hosted CI and branch-rule enforcement remain separate required steps.

## Evidence

- [Audit report](../audits/AUDIT-2026-09-08.md)
- [Existing architecture](../architecture/ARCHITECTURE.md)
- [Existing agent governance research](../research/AGENT-GOVERNANCE-2026-09-08.md)
- [Module contract](../standards/REPOSITORY-AUDIT.md)
- [GitHub reusable workflow context](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use)

## Supersedes / Superseded by

None.
