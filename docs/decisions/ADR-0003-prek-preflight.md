# ADR-0003 — Fast repository pre-flight with prek

Status: Accepted as experimental; initial hosted validation passed.
Date: 2026-09-09.

## Context

Issue [#3](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3) sequences `prek` after the Task command contract so cheap repository mistakes can fail before hosted CI or an agent is used. The repository already owns JSON, file-size, symlink, test, audit, and GitHub workflow checks, so a new hook layer must not repeat all of them.

## Decision

Use prek v0.5.2 with `prek.toml` and bundled, non-mutating hooks only. Add `task preflight`, include it in the local verification contract, and execute it inside the existing GitHub workflow-lint job. Verify the downloaded release archive by SHA-256 and preserve a dedicated log in the existing artifact.

## Alternatives considered

- Python `pre-commit`: compatible and mature, but prek is a single binary and Issue #3 selected it for the cost-aware agent workflow.
- Remote hook repositories: broader ecosystem compatibility, but require network clones and managed environments for checks already available in the pinned binary.
- A separate GitHub job: clearer isolation, but consumes another runner allocation for a fast check that fits the existing workflow-lint trust boundary.
- Formatting hooks: useful later, but automatic rewrites would silently broaden this first integration.

## Consequences

Local commits can receive fast staged-file feedback after `prek install`; full verification checks every tracked file. The configuration is intentionally prek-specific. The private-key detector is heuristic, and the hook set does not replace dedicated secret or workflow-security analysis.

## Evidence

- [Cost-aware architecture baseline](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3)
- [Pre-flight hook contract](../standards/PRE-FLIGHT.md)
- [prek documentation](https://prek.j178.dev/)
- [prek v0.5.2](https://github.com/j178/prek/releases/tag/v0.5.2)

## Supersedes / Superseded by

None.
