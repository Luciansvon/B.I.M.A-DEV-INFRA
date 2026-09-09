# Requests for Comments

RFCs are reviewable proposals for substantial changes to B.I.M.A-DEV-INFRA. They describe a problem, boundaries, rollout order, evidence requirements, and unresolved decisions before implementation becomes a durable shared commitment.

## Lifecycle

```text
Proposed -> Accepted -> Implementing -> Implemented
        \-> Rejected
        \-> Withdrawn
Implemented -> Superseded
```

- **Proposed**: open for review; no implementation commitment.
- **Accepted**: direction approved, but individual phases still require their own evidence.
- **Implementing**: at least one approved phase is in progress.
- **Implemented**: every required acceptance criterion is proven.
- **Rejected**, **Withdrawn**, or **Superseded**: retained for decision history.

Acceptance of a broad RFC does not authorize every tool, workflow, external write, release, deployment, or agent action described in it. Durable shared decisions must be recorded in focused ADRs as they are implemented.

## Naming

```text
RFC-0001-short-title.md
RFC-0002-short-title.md
```

## Index

| RFC | Status | Title |
|---|---|---|
| [RFC-0001](RFC-0001-verification-control-plane.md) | Proposed | Evidence-first verification control plane |
