# ADR-0002 — Cost-aware deterministic command contract

Status: Accepted as experimental; initial hosted validation passed.
Date: 2026-09-09.

## Context

Issue [#3](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3) establishes that scripts and CI should own repetitive verification while agents handle unknown or ambiguous failures. Existing Python audit, regression-test, and actionlint commands were split between documentation and workflow YAML.

## Decision

Use Task as a thin, project-agnostic command contract. The initial contract exposes only implemented operations: test, audit, workflow lint, their combined check, patch whitespace validation, and full verification. GitHub workflows call those commands and remain responsible for tool setup, runner selection, permissions, and artifact upload.

Pin Task v3.53.1. GitHub installs it through `go-task/setup-task` v2.2.0 at full commit `a00fbb05ce67b35648be3c78cbc9fd85354c757e` and verifies the upstream OS-specific archive checksum.

## Alternatives considered

- Keep raw commands only in workflow YAML: preserves duplication and gives humans/agents no stable entry point.
- Introduce Dagger now: explicitly deferred by Issue #3 until the deterministic baseline is stable and portability is justified.
- Add placeholders for build/nightly: rejected because a no-op command could create false evidence.
- Build a custom task runner: duplicates maintained open-source tooling without demonstrated value.

## Consequences

Task becomes one small local prerequisite for the unified command surface. Python audit remains independently runnable. Adding Task does not make verification canonical by itself; `bima-evidence.v1`, security tools, agent packets, and measured value remain later increments.

## Evidence

- [Cost-aware architecture baseline](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3)
- [Command contract](../standards/COMMAND-CONTRACT.md)
- [Task documentation](https://taskfile.dev/docs/)
- [Task command validation](../audits/VALIDATION-2026-09-09-TASKFILE.md)

## Supersedes / Superseded by

None.
