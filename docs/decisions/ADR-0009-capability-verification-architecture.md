# ADR-0009 — Capability-based verification with explicit authority

Status: **Accepted architecture baseline; new runtime capabilities are not implemented.**
Date: 2026-09-10.
Decision owner: Bima, through the request to audit all plans and establish the architecture; Solo execution.

## Context

Issues [#3](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3), [#8](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/8), [#9](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/9), [#15](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/15), [#17](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/17) and [RFC-0001](../rfcs/RFC-0001-verification-control-plane.md) overlap but disagree on delivery order, verdict semantics and provider readiness. The implemented baseline at `006d782114c9667b8dbe7edaf37601c36667ba43` is the beta repository audit with v1 evidence and bounded routing. A fixture and AI-COLOR-COMPARE are already consumers.

The [plan audit](../audits/ARCHITECTURE-PLAN-AUDIT-2026-09-10.md) and [52-source ledger](../research/SOURCES-ARCHITECTURE-2026-09-10.md) support resolving contracts before expanding execution or model use. Source review does not establish any provider's measured superiority.

## Decision

1. **Deployment:** retain Local + GitHub Actions. Implement shared capabilities as small CLI modules invoked by Task/reusable workflows. Logical layers do not imply separate services. No daemon, Docker installation, multi-CI migration, generic plugin loader or dashboard is required by this decision.
2. **Authority:** trusted policy authorizes each operation before execution; a trusted adapter normalizes native results and policy evaluates required checks afterward. Apply authorization again to retries, patches, sandbox creation, promotion and publication. A provider's availability or an agent's recommendation grants no permissions.
3. **Verification:** run a verifier inside an authorized execution environment. GitHub Actions is the authoritative CI publication path; the truth claim comes from the reviewed verifier, declared scope, subject identity and retained evidence. A green provider job alone is insufficient. Hardware/GUI proof must name its actual environment.
4. **State:** retain native attempt outcomes. The target aggregate verdict is `PASS | FAIL | UNKNOWN | BLOCKED`; `FLAKY` is a separate stability classification derived from equivalent attempts or a reviewed scoped registry. A human report may display FLAKY, but it is not a replacement for the underlying attempt results. Warnings, skips and waivers remain explicit metadata. Missing required evidence never passes.
5. **Evidence:** preserve the current `bima-evidence.v1` and `bima-agent-packet.v1` bytes, schemas and status meanings. A v2 envelope is a future additive migration with consumer fixtures, not an immediate schema edit. Native SARIF/JUnit/SBOM/provenance remain referenced. Semantic result identity stays separate from run timestamps, budget counters and volatile provider metadata.
6. **Memory:** reviewed project records remain authoritative; SQLite + FTS5 is the selected rebuildable local index when retrieval is implemented. Records need reproduced failure, confirmed cause, scoped fix and relevant re-verification, plus reviewer/provenance and invalidation. A passing run alone does not prove causality. Live database/cache files stay outside OneDrive and other synchronized/network directories.
7. **Intelligence:** rules and reviewed retrieval precede model escalation. Optional local SLMs are benchmark candidates, not a mandatory hop. Authorized complex work can go directly to a strong agent. No model family, parameter count or hardware becomes a global architecture dependency; #9's <2B target remains a specialized pilot constraint.
8. **Providers:** native search is the context baseline. Graphify is an opt-in code-only A/B candidate; semantic/document extraction needs its own permission/cost test. Hosted sandbox, durable orchestration, database branching, security response and project UI default to disabled. Name contracts now; implement only interfaces required by a real pilot.
9. **ReleaseProof:** preserve the provenance-versus-behavior split and same-artifact identity. Its implementation remains gated by #8's real case and reuse/demand validation. It does not block failure normalization, memory record collection or an independent context experiment.
10. **Delivery:** follow [NEXT](../NEXT.md): existing governance decisions; executable project/policy contract; one real failure-normalization adapter plus v2 migration; reviewed memory retrieval; independent gated experiments. Neither Graphify nor ReleaseProof is a prerequisite for the other or for core verification.

The normative target behavior is in [CAPABILITY-CONTRACT](../architecture/CAPABILITY-CONTRACT.md). It is an implementation specification, not a claim of an already enforced Policy Gate.

## Alternatives considered

| Alternative | Decision and reason |
|---|---|
| Adopt #17 verbatim | Revise: clarify repeated authorization, failure aggregation, enforcement and v1 migration. |
| Implement RFC-0001 ReleaseProof-first | Defer that ordering: #8's development gate is still unmet; use a real test/log adapter first. |
| Implement Graphify-first from #15 | Keep an independent experiment; no measured context bottleneck justifies blocking core contracts. |
| Implement every named provider | Reject: ownership, secrets, cleanup and maintenance costs would grow before consumer evidence. |
| OPA service immediately | Defer: initial deterministic policy can reuse the current standard-library approach; adopt OPA if tested rule reuse warrants it. |
| Boolean results or one five-state field | Reject: check outcome, execution availability, stability and authorization have distinct meanings. |
| Replace v1 in place | Reject: existing canonicalizer and packet readers reject extra fields/statuses and consumer pins are deployed. |
| Shared graph/vector database now | Defer: reviewed corpus and lexical baseline measurements must come first. |
| Automatic model-training pipeline | Defer: valid labels, held-out evaluation and total-cost benefit have not been established. |

## Consequences

There is one architecture owner document and one delivery order. Application commands and domain expectations remain project-owned. The first runtime increments can use the existing Python standard library and JSON contracts without forcing consumers into Python. Future language/provider changes remain possible through versioned inputs and outputs.

This decision deliberately adds design work before privileged execution. It does not activate branch settings, select a code license, install providers, train a model, change a consumer pin or authorize publishing. Existing governance choices remain visible and do not block documentation or unprivileged local development.

## Evidence

- [Plan audit, source snapshot and validation](../audits/ARCHITECTURE-PLAN-AUDIT-2026-09-10.md)
- [Primary-source ledger](../research/SOURCES-ARCHITECTURE-2026-09-10.md)
- [Existing consumer evidence](../audits/VALIDATION-2026-09-09-AI-COLOR-CONSUMER.md)
- [Existing evidence contract](../standards/EVIDENCE-CONTRACT.md)
- [Existing packet contract](../standards/AGENT-PACKET.md)
- [GKI-0001: evidence input line endings](../incidents/GLOBAL-KNOWN-ISSUES.md)

## Supersedes / Superseded by

Supersedes RFC-0001's proposed delivery order and mixed status model, #15's strict experiment chain, and #17's ambiguous single verdict axis for the accepted target architecture. The original research and proposals remain historical evidence. Extends #3's machine-first principle. Preserves ADR-0001 through ADR-0008 implementation contracts, especially ADR-0007 and ADR-0008; no v1 wire-format migration is performed here.
