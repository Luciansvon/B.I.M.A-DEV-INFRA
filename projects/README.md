# Project Registry

This directory is an **index/pointer layer**, not a place to copy every project's source code or full documentation.

## Rule

Each consuming project keeps its live architecture and incident history in its own repository.

B.I.M.A-DEV-INFRA may keep a lightweight registry entry containing:

```text
project name
repository URL
project type
shared workflows used
runner profile
project architecture link
project incident/issue link
last integration review
```

## Why

This preserves a central view without creating two competing sources of truth.

```text
B.I.M.A-DEV-INFRA
   |
   +-- global standards
   +-- reusable workflows
   +-- global known issues
   +-- project registry --------+
                                |
             +------------------+------------------+
             v                  v                  v
          Project A          Project B          Project C
          architecture       architecture       architecture
          incidents          incidents          incidents
```

## Promotion

When a project lesson is promoted to global knowledge, the global entry should link to the originating project issue/incident. Do not duplicate the entire project incident history here.

Use templates from:

- `templates/project/ARCHITECTURE.md`
- `templates/project/INCIDENTS.md`
