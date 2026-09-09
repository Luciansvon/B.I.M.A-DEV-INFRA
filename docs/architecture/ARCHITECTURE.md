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
      Reusable Workflow
              |
      +-------+-------+
      |               |
      v               v
GitHub Runner    Self-hosted Runner
      |               |
      +-------+-------+
              |
              v
    Shared Module / Adapter
              |
              v
 Test / Benchmark / Audit / Build / Deploy
              |
              v
 Evidence: report / artifact / status / release
```

## Layers

### 1. Trigger layer

Events from Git, manual dispatch, API/webhooks, schedules, issues, pull requests, or external integrations.

### 2. Orchestration layer

Reusable GitHub workflows coordinate execution. They should remain project-agnostic and accept configuration through explicit inputs.

### 3. Execution layer

- GitHub-hosted runner for generic reproducible jobs.
- Self-hosted runner when local hardware, persistent model/cache, devices, operating systems, or private infrastructure matter.

### 4. Adapter layer

Project-specific commands are passed through a documented contract instead of hard-coding application architecture into shared infrastructure.

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

The initial normalization path keeps semantic comparison separate from execution-specific details:

```text
module result.json
       |
       +--> canonical.json ------> stable SHA-256 comparison
       |
       +--> execution.json ------> timestamp, runtime, raw-input SHA-256
       |
       +--> non-pass only -------> bounded routing packet
```

The current adapter covers repository audit evidence. Other modules must map into the versioned envelope explicitly rather than copying raw runner metadata into canonical fields.

The routing packet separates deterministic findings from errors that may need reasoning. It never invokes an agent: `fail` stays in the machine lane, `error` only marks agent-escalation eligibility, and `pass` creates no packet.

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
