# Project Integration Contract

Projects consuming B.I.M.A-DEV-INFRA keep their own architecture and incident history, but expose enough metadata for shared workflows to operate safely.

Target semantics are governed by [ADR-0009](../decisions/ADR-0009-capability-verification-architecture.md) and [CAPABILITY-CONTRACT](CAPABILITY-CONTRACT.md). Current executable integration includes the [repository-audit v1 interface](../standards/REPOSITORY-AUDIT.md), its narrow [Policy Gate v1](../standards/POLICY-GATE.md), and the [trusted reusable launcher](../standards/TRUSTED-POLICY-LAUNCHER.md). Policy Gate v1 authorizes only repository audit; it is not a generic application-command interface.

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

## Required fields and staged implementation

The initial strict versioned JSON profile and compatibility fixtures are implemented for `repository-audit.v1`. Earlier `.bima/project.yml` examples remain proposals, not supported executable inputs. The broader fields below remain requirements for future operation classes; their presence here is not a claim that arbitrary build/test/release commands are executable.

- Project identity, exact source revision and expected artifact identity.
- Named commands/approved script references, required versus optional checks, expected output formats and meaningful test-count expectations.
- Runner OS/architecture, relevant environment/toolchain/fixture constraints and resource limits.
- Scoped writable outputs, approved network/credential needs, evidence sensitivity, retention owner and cleanup requirements.
- Trusted policy reference and requested operation scope. Actor identity/approval are supplied by the trusted executor, never self-asserted by project content.
- Byte-hashed text inputs normalized explicitly, such as LF `.gitattributes` rules; see [GKI-0001](../incidents/GLOBAL-KNOWN-ISSUES.md).

Schema-valid project commands remain executable untrusted code until the runner trust boundary permits them. Advisory discovery cannot execute them or override explicit declarations. Required missing checks/providers cannot become successful through fallback. Optional unavailable capabilities must remain visible, and a passing required scope must not imply those optional checks passed.

Project-owned private evidence remains under the project's access policy. Shared memory contains only approved portable cases/references; live indexes/caches stay outside synchronization folders. New schemas and consumer pin changes require the migration evidence described in [CAPABILITY-CONTRACT](CAPABILITY-CONTRACT.md).

Optional capability requests use the [experiment gate](../standards/EXPERIMENT-GATE.md). A project declaration is demand evidence, not execution permission. Readiness requires independently reviewed demand from at least two distinct project repositories, then separate Policy Gate authorization.
