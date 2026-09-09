# ADR-0005 — Enforce full-SHA Action references offline

Status: Accepted as experimental; hosted validation pending.
Date: 2026-09-09.

## Context

Issue [#3](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3) sequences pinact after action-validator. The security baseline already requires full commit SHAs, but enforcement depended on human review and the workflows' current text.

## Decision

Use pinact v4.1.1 through prek with `--fix=false --no-api`. Check only workflow and local Action files selected by the shared pre-flight configuration. Install checksum-verified standalone binaries locally and in the existing workflow-lint job.

## Alternatives considered

- Automatic pinning in CI: rejected because CI must not rewrite or push source implicitly.
- Online comment/tag verification on every run: stronger metadata validation, but adds API availability, rate-limit, and credential dependencies to the fast deterministic gate.
- Repository ruleset enforcement only: useful later, but current settings do not enable SHA pin enforcement and local feedback would still be absent.
- Custom regular-expression scanner: rejected because it would duplicate pinact's parser and reference handling.

## Consequences

Mutable tags fail locally and in CI without network access. Dependabot continues to propose reviewable Action updates. Version comments and SHA provenance are not verified by this offline increment and must not be claimed as covered.

## Evidence

- [Cost-aware architecture baseline](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3)
- [Action pinning contract](../standards/ACTION-PINNING.md)
- [pinact repository](https://github.com/suzuki-shunsuke/pinact)
- [pinact v4.1.1](https://github.com/suzuki-shunsuke/pinact/releases/tag/v4.1.1)

## Supersedes / Superseded by

None.
