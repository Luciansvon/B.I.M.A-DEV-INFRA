# Architecture Decision Records

Use ADRs for durable shared decisions that affect B.I.M.A-DEV-INFRA architecture, contracts, security, runner policy, evidence format, or reusable workflow behavior.

## Naming

```text
ADR-0001-short-title.md
ADR-0002-short-title.md
```

## Template

```md
# ADR-0001 — Title

Status: Proposed | Accepted | Superseded | Rejected
Date: YYYY-MM-DD

## Context
What problem or constraint requires a decision?

## Decision
What is being decided?

## Alternatives considered
What other options were evaluated?

## Consequences
Positive and negative effects.

## Evidence
Research, incidents, benchmarks, PRs, or experiments supporting the decision.

## Supersedes / Superseded by
Links when applicable.
```

## What belongs here

Examples:

- runner isolation policy
- result schema choice
- reusable workflow versioning policy
- action pinning policy
- model/artifact storage boundary
- cross-project security requirements

Project-only decisions belong in the project repository.
