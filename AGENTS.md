# AGENTS.md

## Purpose

This repository is project-agnostic infrastructure. Keep shared rules, reusable workflows, cross-project knowledge, and reusable failure patterns here. Keep application-specific implementation details in the owning project repository.

## Required reading before changes

1. `README.md`
2. `docs/architecture/ARCHITECTURE.md`
3. `docs/architecture/PROJECT-CONTRACT.md`
4. Relevant ADRs in `docs/decisions/`
5. Relevant known issues in `docs/incidents/`

## Core rules

- Reusable before duplicated.
- Global knowledge only when it applies across projects or infrastructure itself.
- Project-specific architecture, constraints, and incidents stay with that project.
- Promote a project lesson to global knowledge when the same root cause appears in 2 or more projects, or when the failure is clearly caused by shared infrastructure.
- Do not store secrets, production databases, large AI model weights, or unrelated binaries in Git.
- Workflows must use least privilege, explicit timeouts, clear inputs/outputs, and reproducible versions.
- A workflow is not complete until it produces evidence: test result, report, artifact, status, benchmark, or log.
- Do not silently change shared contracts. Record architecture-impacting decisions as ADRs.
- Do not rewrite research source ledgers without preserving prior evidence.
- Do not mark work complete when required validation is missing or blocked.

## Incident routing

```text
FAILURE
  |
  v
PROJECT INCIDENT / ISSUE
  |
  v
ROOT CAUSE
  |
  +--> project-specific --> keep in project
  |
  +--> shared infra OR repeated in >=2 projects
             |
             v
      GLOBAL KNOWN ISSUE
             |
             v
  prevention / workflow / rule update
```

## Architecture routing

- `docs/architecture/` = shared B.I.M.A-DEV-INFRA architecture and project integration contracts.
- Project repository = application/domain architecture.
- `docs/decisions/` = why shared architectural decisions exist.

## Change policy

For shared workflow changes, document:

- purpose
- inputs
- outputs
- permissions
- runner requirements
- failure conditions
- produced evidence
- compatibility or migration impact

Follow `docs/standards/WORKFLOW-CONTRACT.md`.
