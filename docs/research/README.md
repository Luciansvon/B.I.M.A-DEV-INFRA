# Research Index

## 2026-09-08 — GitHub Beyond App Builds

**Total unique retained/reviewed sources across the full conversation session: 160.**

| Document | Purpose | Sources |
|---|---|---:|
| [`GITHUB-USE-CASES-2026-09-08.md`](./GITHUB-USE-CASES-2026-09-08.md) | Cross-domain findings, patterns, anti-patterns, and project ideas | synthesis |
| [`SOURCES-2026-09-08.md`](./SOURCES-2026-09-08.md) | Main deep-pass source ledger | 130 |
| [`SOURCES-EARLIER-SESSION-2026-09-08.md`](./SOURCES-EARLIER-SESSION-2026-09-08.md) | Earlier-turn sources from the same session not duplicated in the deep pass | 30 |

```text
130 deep-pass sources
+30 earlier-session unique sources
=160 total unique retained/reviewed sources
```

## 2026-09-08 — Agent Governance, Rules, Skills, and Enforcement

A separate focused pass tested whether B.I.M.A-DEV-INFRA should use Agent Skills and how they should interact with repository rules, architecture/error memory, hooks, scripts, and CI gates.

| Document | Purpose | Sources |
|---|---|---:|
| [`AGENT-GOVERNANCE-2026-09-08.md`](./AGENT-GOVERNANCE-2026-09-08.md) | Findings and recommended layered agent-governance architecture | synthesis |
| [`SOURCES-AGENT-GOVERNANCE-2026-09-08.md`](./SOURCES-AGENT-GOVERNANCE-2026-09-08.md) | Community + official + real-repository source ledger | 69 |

Key conclusion:

```text
GUIDANCE    -> AGENTS.md / path instructions
PROCEDURE   -> Agent Skills
ENFORCEMENT -> hooks / scripts / CI / repository rules
MEMORY      -> architecture / ADR / incidents
EVIDENCE    -> tests / logs / reports / artifacts
```

The 69-source focused pass overlaps thematically with the earlier 160-source GitHub research and is tracked as its own research set rather than being added arithmetically to the prior unique-source count.

## 2026-09-13 — Optional Spec Kit authoring adapter

This pass evaluates Spec Kit as a provider-neutral authoring layer below B.I.M.A governance and above deterministic verification. It does not activate a package, preset, workflow, adapter, or consumer.

| Document | Purpose | Sources |
|---|---|---:|
| [`SOURCES-SPEC-KIT-ADAPTER-2026-09-13.md`](./SOURCES-SPEC-KIT-ADAPTER-2026-09-13.md) | Pinned upstream, community, standards, platform, and research evidence | 74 |

Future research passes should create dated ledgers instead of silently replacing these files. That preserves how conclusions changed as GitHub features, agent tooling, pricing, community practices, and deprecations evolve.
