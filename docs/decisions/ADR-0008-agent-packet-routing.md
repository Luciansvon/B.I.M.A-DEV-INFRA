# ADR-0008 — Route bounded failures before agent escalation

Status: Accepted as experimental; initial hosted validation passed.
Date: 2026-09-09.

## Context

Issue [#3](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3) requires a small failure packet containing only the context needed to route a failed stage. Sending every result or raw log to an agent would increase cost, expose untrusted content, and waste model calls on deterministic findings that already have machine-readable codes.

## Decision

Add `bima-agent-packet.v1` and a standard-library adapter for canonical repository-audit evidence. A completed audit with known findings routes to `machine`; an unclassified audit infrastructure error routes to `agent`; a pass creates no packet. Bound lists and strings, hash both canonical input and packet output, clear stale owned outputs, and never invoke an agent automatically.

## Alternatives considered

- Send all failures directly to an agent: rejected because known hygiene findings need no model reasoning.
- Include raw logs and complete evidence: rejected because it defeats the bounded-context and untrusted-data boundary.
- Retry automatically: rejected because repeatability has not been measured and retries can hide deterministic failures.
- Infer changed targets from finding paths: rejected because the current canonical evidence does not contain a reviewed diff or changed-file set.
- Add another GitHub Actions job: rejected because packet generation is inexpensive and belongs beside the existing canonicalization step.

## Consequences

Failed runs can carry a deterministic, inspectable handoff without spending agent tokens. Consumers must still decide whether and how to act; `route=agent` is data, not authority. Version 1 covers only repository audit and cannot claim generic failure routing for builds, tests, benchmarks, releases, or deployments.

## Evidence

- [Bounded agent packet contract](../standards/AGENT-PACKET.md)
- [Canonical evidence contract](../standards/EVIDENCE-CONTRACT.md)
- [Validation record](../audits/VALIDATION-2026-09-09-AGENT-PACKET.md)

## Supersedes / Superseded by

None.
