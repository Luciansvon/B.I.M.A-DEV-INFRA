# ADR-0006 — Analyze GitHub automation security offline

Status: Accepted as experimental; initial hosted validation passed.
Date: 2026-09-09.

## Context

Issue [#3](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3) sequences zizmor after immutable Action-reference enforcement. Syntax, schemas, path globs, and SHA shape are already checked, but those tools do not analyze dangerous triggers, template injection, permissions, credential persistence, or Dependabot security posture.

## Decision

Use zizmor v1.30.0 through prek with strict collection, the default regular persona, and fully offline read-only execution. Reuse the existing workflow-lint job and retained pre-flight log. Remediate its initial medium Dependabot-cooldown finding with `default-days: 7`.

## Alternatives considered

- Official zizmor Action plus SARIF: richer GitHub presentation, but adds Actions and write permission before a need for Code Scanning integration is established.
- Online audits with `GITHUB_TOKEN`: broader metadata checks, but adds API availability, rate-limit, and token behavior to the deterministic fast gate.
- Auditor or pedantic persona: broader review surface with greater false-positive tolerance; unsuitable as the first blocking baseline.
- Custom workflow-security scanner: duplicates a maintained domain-specific analyzer.

## Consequences

Locally decidable GitHub automation findings fail before agent escalation without adding Docker, credentials, mutation, or a runner job. Online-only checks and more aggressive personas remain outside the gate and must not be claimed as covered.

## Evidence

- [Cost-aware architecture baseline](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3)
- [Workflow-security contract](../standards/WORKFLOW-SECURITY.md)
- [zizmor documentation](https://docs.zizmor.sh/)
- [zizmor v1.30.0](https://github.com/zizmorcore/zizmor/releases/tag/v1.30.0)
- [GitHub Dependabot cooldown documentation](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/optimizing-pr-creation-version-updates#setting-up-a-cooldown-period-for-dependency-updates)

## Supersedes / Superseded by

None.
