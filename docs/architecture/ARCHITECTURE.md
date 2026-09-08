# Shared Architecture

## Scope

This document describes the architecture of **B.I.M.A-DEV-INFRA itself**, not the internals of every project that consumes it.

```text
PROJECT / HUMAN / API / SCHEDULE
              |
              v
         GitHub Event
              |
              v
      Thin GitHub Workflow
              |
              v
    GitHub-hosted Dagger Engine
              |
              v
      B.I.M.A core module
  audit / lint / test / security
  build / package / benchmark
              |
              v
       Normalized evidence
              |
       +------+------+
       |             |
       v             v
 GitHub adapter   Windows adapter
 release/upload   build/sign/package
```

Initial execution scope is GitHub-hosted only. A local Dagger runtime, Azure Pipelines, GitLab CI, and self-hosted execution remain deferred until a demonstrated workload justifies their operational cost.

## Layers

### 1. Trigger layer

Events from Git, manual dispatch, API/webhooks, schedules, issues, pull requests, or external integrations.

### 2. Orchestration layer

Thin GitHub workflows trigger pinned Dagger commands and preserve their evidence. Pipeline logic belongs in reusable modules rather than duplicated workflow YAML.

### 3. Execution layer

- GitHub-hosted Ubuntu runner and its Dagger Engine for the initial portable core.
- Native GitHub-hosted Windows jobs are platform adapters when Windows packaging or signing cannot run inside the portable core.
- Self-hosted runners remain future adapters for local hardware, persistent model/cache, devices, or private infrastructure.

### 4. Adapter layer

Project inputs are passed through documented contracts instead of hard-coding application architecture into shared infrastructure. Publishing, signing, store upload, and deployment remain explicit platform adapters because their credentials and APIs differ.

### 5. Evidence layer

Every meaningful workflow should produce inspectable evidence such as:

- checks/status
- logs
- `result.json`
- benchmark data
- test reports
- artifacts
- release metadata
- provenance/SBOM where relevant

## Knowledge ownership

```text
GLOBAL / SHARED                       PROJECT LOCAL
----------------                      ----------------
workflow architecture                 app architecture
runner policy                         domain modules
security baseline                     app constraints
result schemas                        project test cases
cross-project incident patterns       project incidents
shared ADRs                           project ADRs
```

## Promotion rule

A project-specific lesson becomes global when:

1. the same root cause appears in at least 2 projects; or
2. the root cause belongs to shared infrastructure; or
3. prevention requires changing a shared workflow, runner, contract, or security rule.

Do not promote merely because an error looks similar. Root cause must match.

## Non-goals

B.I.M.A-DEV-INFRA is not:

- a monorepo containing every application
- a production database
- a model registry for multi-GB weights
- a media archive
- a replacement for project-specific architecture documentation
