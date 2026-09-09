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

## Registered consumers

| Project | Repository | Type | Shared workflow | Runner | Project source of truth | Last integration review |
|---|---|---|---|---|---|---|
| AI-COLOR-COMPARE | [Repository](https://github.com/Luciansvon/AI-COLOR-COMPARE) | React/Vite/Tauri Studio Color QC with an Android pilot | `repository-audit` beta, pinned to `dc7a96cf885f41bd665270c4a77ef0e7c12d313b` | GitHub-hosted Ubuntu 24.04 | [README](https://github.com/Luciansvon/AI-COLOR-COMPARE/blob/main/README.md), [project issues](https://github.com/Luciansvon/AI-COLOR-COMPARE/issues) | 2026-09-09; [evidence](../docs/audits/VALIDATION-2026-09-09-AI-COLOR-CONSUMER.md) |
