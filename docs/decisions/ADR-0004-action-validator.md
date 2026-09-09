# ADR-0004 — Complement actionlint with action-validator

Status: Accepted as experimental; initial hosted validation passed.
Date: 2026-09-09.

## Context

Issue [#3](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3) sequences action-validator after prek. Actionlint already checks GitHub workflow syntax, expressions, and shell integration, but the baseline also requires published-schema validation and detection of path filters that match no repository files.

## Decision

Use action-validator v0.9.0 as a local prek system hook for GitHub workflow and local Action YAML. Keep actionlint. Install the official checksum-verified Linux binary in the existing workflow-lint job and preserve its output within the existing pre-flight evidence artifact.

## Alternatives considered

- Replace actionlint: rejected because the tools cover overlapping but different failure classes.
- Use the upstream composite Action: functional, but adds an Action/cache dependency when a checksum-verified standalone binary is sufficient.
- Create another CI job: rejected because this fast check fits the existing workflow-lint job and trust boundary.
- Build a custom schema validator: rejected because it would duplicate maintained tooling.

## Consequences

Workflow schema errors and stale path globs can fail before agent escalation. Local users need action-validator on `PATH`; Windows has a one-time Cargo or NPM installation because v0.9.0 publishes no Windows binary. Current workflows contain no `paths` filters, so the first repository run validates schemas but does not exercise glob matching.

## Evidence

- [Cost-aware architecture baseline](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3)
- [Workflow schema contract](../standards/WORKFLOW-SCHEMA.md)
- [action-validator repository](https://github.com/mpalmer/action-validator)
- [action-validator v0.9.0](https://github.com/mpalmer/action-validator/releases/tag/v0.9.0)

## Supersedes / Superseded by

None.
