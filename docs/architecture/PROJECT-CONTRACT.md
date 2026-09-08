# Project Integration Contract

Projects consuming B.I.M.A-DEV-INFRA keep their own architecture and incident history, but expose enough metadata for shared workflows to operate safely.

## Minimum project metadata

Each project should document or provide:

```text
project name
repository
project type
supported platforms
runtime/toolchain versions
build command
lint command
unit-test command
integration-test command
benchmark command (if applicable)
artifact paths
runner requirements
required services/devices
release strategy
known project constraints
```

## Ownership

The project repository owns:

- `ARCHITECTURE.md`
- project ADRs
- project-specific `INCIDENTS.md` or Issues
- domain-specific test cases
- application configuration

B.I.M.A-DEV-INFRA owns:

- reusable workflow implementation
- global workflow contracts
- shared security baseline
- runner policies
- shared evidence/result schemas
- cross-project known issues

## Project adapter principle

Shared workflows must not need to understand an application's internal module graph.

Prefer:

```text
shared workflow
    |
    +-- input: test_command
    +-- input: artifact_path
    +-- input: runner_label
    +-- input: config
```

Avoid:

```text
shared workflow
    |
    +-- hard-coded knowledge of Project A internals
    +-- Project B exception
    +-- Project C exception
```

If many projects require the same exception, promote it into a reusable capability rather than branching by project name.

## Incident promotion

Project incident -> root cause confirmed -> check global incident index.

Promote when the same root cause affects >=2 projects or belongs to shared infra. When promoted, link back to affected project incidents instead of copying their entire histories.
