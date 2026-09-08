# Agent Governance Research — 2026-09-08

## Question

What should B.I.M.A-DEV-INFRA use to guide coding agents reliably across different future projects: `AGENTS.md`, path instructions, Agent Skills, hooks/scripts/CI, architecture docs, incident memory, or some combination?

This research intentionally did **not** assume one current project, one programming language, or one AI agent.

## Research method

The pass reviewed **50+ relevant sources** across:

- Reddit communities discussing Claude Code, GitHub Copilot, Codex, LocalLLaMA, AI agents, and agent workflows.
- Current GitHub and VS Code documentation.
- The Agent Skills open specification.
- OpenAI material and public Codex repositories.
- Real repositories that maintain `AGENTS.md` plus `.agents/skills`.
- GitHub Copilot hook documentation and real hook examples.

The complete retained source ledger is in `SOURCES-AGENT-GOVERNANCE-2026-09-08.md`.

---

# Executive conclusion

B.I.M.A-DEV-INFRA should **not** choose between rules and skills. It needs a layered system because each primitive solves a different failure mode.

```text
                    HUMAN INTENT
                         |
                         v
                    AGENTS.md
          minimal always-relevant rules
                         |
          +--------------+--------------+
          |                             |
          v                             v
  path instructions                 Skills
 context by repository area   task-specific playbooks
          |                             |
          +--------------+--------------+
                         |
                         v
                deterministic layer
             hooks / scripts / CI gates
                         |
                         v
                 evidence + memory
       architecture / ADR / incidents / reports
```

Recommended mental model:

| Layer | Purpose | Reliability role |
|---|---|---|
| `AGENTS.md` | Small repository-wide operating contract | Steering |
| Path instructions | Rules/context that only matter to certain files/areas | Steering |
| `SKILL.md` | Repeatable task procedures loaded on demand | Procedure |
| Hooks/scripts/CI | Rules that must be mechanically enforced | Enforcement |
| Architecture/ADR | Durable system and decision memory | Memory |
| Incidents/known issues | Failure history and reusable lessons | Memory/evidence |

---

# Finding 1 — Agent Skills are justified

Agent Skills are no longer merely a vendor-specific prompt convention. The Agent Skills specification defines a portable `SKILL.md` package with optional scripts, references, and assets. GitHub Copilot and VS Code support the standard, GitHub accepts project skills under `.github/skills`, `.claude/skills`, or `.agents/skills`, and Codex uses repository skills under `.agents/skills`.

Skills are appropriate when a task has a **repeatable procedure** that should not occupy every agent session's context.

Examples relevant to DEV-INFRA:

- workflow audit
- benchmark execution
- incident triage
- research update
- release verification
- architecture synchronization
- dependency/security review
- hardware test procedure

Do **not** create a skill merely because instructions can be written. A skill is justified when the task has a stable trigger and a meaningful playbook, especially if it benefits from scripts/templates/references.

---

# Finding 2 — Keep AGENTS.md small

A repeated community failure pattern is treating `CLAUDE.md`/`AGENTS.md` as an encyclopedia. Large always-loaded instruction files consume context and still do not guarantee compliance.

Real repositories using skills successfully tend to keep `AGENTS.md` as:

1. repository identity / scope,
2. global non-negotiable behavioral guidance,
3. navigation/index to specialized skills and documentation,
4. a small number of commands and invariants.

Conditional procedures belong in skills or focused documentation.

For DEV-INFRA, `AGENTS.md` should not absorb benchmark methodology, full incident procedures, release procedures, or every known error.

---

# Finding 3 — Prompt instructions are not enforcement

This was the strongest correction to the earlier design.

Community reports repeatedly show agents can acknowledge a rule and still violate it later, especially in long sessions. A rule stated in Markdown remains part of probabilistic model behavior.

Therefore:

```text
"Prefer X"
"When doing Y, follow this workflow"
        -> instruction / skill

"Never push directly to main"
"Never expose a secret"
"This schema must validate"
"This workflow must pass before merge"
        -> deterministic check / permission / hook / CI gate
```

GitHub Copilot now officially supports hooks with lifecycle events such as `preToolUse`, and hooks can programmatically approve/deny tool execution. GitHub's own examples include tool guardians, secret scanners, import/package validation, and governance auditing.

Cross-agent portability still matters: Copilot hooks are not automatically Codex/Claude hooks. For critical repository guarantees, **CI, branch rules, scripts, and validators remain the portable final gate** even if agent-specific hooks are added for faster feedback.

---

# Finding 4 — `.agents/skills` is the best canonical skill location for this repo

Current GitHub documentation accepts `.agents/skills` for project skills, VS Code treats Agent Skills as an open standard, and Codex natively scans `.agents/skills` in repository ancestors.

This makes `.agents/skills` the strongest canonical location for a project-agnostic infrastructure repo.

However, compatibility is not perfectly universal. Some agent ecosystems still have their own discovery paths or legacy behavior. Do not maintain multiple divergent copies manually.

Recommended strategy:

```text
.agents/skills/        <- canonical source
        |
        +-> compatibility link/copy only when required
```

If a future agent requires `.claude/skills` or another location, generate/sync that representation instead of editing two independent copies.

---

# Finding 5 — Skills themselves need testing

A skill can be malformed, trigger too often, fail to trigger, contain platform-specific assumptions, or consume excessive context.

Community practitioners are beginning to treat skills like software:

- positive trigger prompts: should load skill
- negative trigger prompts: should not load skill
- output-quality checks
- platform checks (Windows/Linux differences)
- token/context cost
- deterministic script tests
- revalidation when model/harness changes

DEV-INFRA should eventually have skill validation, but this does **not** mean building a giant skill benchmark framework before the first useful skill exists.

Recommended progression:

```text
create useful skill
      |
use it on real tasks
      |
collect failures
      |
add focused eval cases
      |
only automate recurring evals
```

---

# Finding 6 — Skills should use progressive disclosure

The strongest common pattern across the specification, GitHub examples, Codex behavior, and community experience is:

```text
SKILL.md
  -> short core workflow
  -> links only to relevant references
  -> scripts for deterministic operations
  -> templates/assets only when required
```

Avoid a skill that immediately loads a library of unrelated documents.

Suggested form:

```text
.agents/skills/workflow-audit/
├── SKILL.md
├── scripts/
│   └── validate-workflow.py
├── references/
│   ├── permissions.md
│   └── workflow-contract.md
└── templates/
    └── audit-report.md
```

---

# Finding 7 — Architecture and incident memory should remain separate from skills

A skill is a procedure, not the primary historical memory store.

Correct separation:

```text
docs/architecture/
    -> what the shared system is

docs/decisions/
    -> why important choices were made

docs/incidents/
    -> what failed, root cause, prevention

.agents/skills/
    -> how an agent performs recurring tasks
```

A skill may reference architecture or incident documents when required, but should not duplicate their contents.

This validates the hybrid project/global memory model already adopted in DEV-INFRA.

---

# Finding 8 — Do not create specialized agents yet unless a role needs unique tools

Custom agents/subagents become useful when a task needs a distinct tool set, permission boundary, model, or persistent role.

A separate "researcher", "reviewer", or "architect" agent is not automatically better than one capable agent using focused skills.

Recommended decision rule:

```text
Need reusable procedure only?
    -> Skill

Need always-on repository rule?
    -> AGENTS.md / instructions

Need deterministic restriction/check?
    -> hook/script/CI/ruleset

Need different tools/permissions/context isolation?
    -> specialized agent/subagent
```

For the current DEV-INFRA maturity, skills are higher priority than creating a fleet of personas.

---

# Recommended architecture for B.I.M.A-DEV-INFRA

```text
B.I.M.A-DEV-INFRA/
|
├── AGENTS.md
│   # short repository contract + skill index
│
├── .github/
│   ├── copilot-instructions.md
│   ├── instructions/
│   │   ├── workflows.instructions.md
│   │   └── docs.instructions.md
│   └── hooks/                     # only Copilot-specific fast feedback where useful
│
├── .agents/
│   └── skills/                    # canonical cross-agent skill source
│       ├── workflow-audit/
│       ├── incident-triage/
│       ├── research-update/
│       ├── benchmark/
│       └── architecture-sync/
│
├── scripts/                       # deterministic reusable validators
│
├── .github/workflows/             # portable CI enforcement
│
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── incidents/
│   ├── standards/
│   └── research/
│
└── projects/                      # registry/pointers, not duplicated application internals
```

---

# Which skills should exist first?

Research supports starting small.

## P0 — research-update

Why first: this repository is explicitly research-backed and future decisions must preserve source provenance.

Responsibilities:

- detect ambiguity/uncertainty
- research before deciding
- prioritize current official sources + community experience
- retain source ledger
- distinguish fact vs opinion
- flag stale/deprecated information
- update research conclusions without erasing history

## P0 — workflow-audit

Responsibilities:

- validate reusable-workflow contract
- inspect permissions and least privilege
- inspect triggers and untrusted-input boundaries
- check timeout/concurrency/artifacts
- check Action pinning/version policy
- verify evidence/output contract
- identify accidental project-specific coupling

## P1 — incident-triage

Responsibilities:

- capture symptom/reproduction/environment/evidence
- identify root cause
- check known incidents
- decide project-local vs shared root cause
- promote reusable failures to global known issues only when promotion criteria are met

## P1 — architecture-sync

Responsibilities:

- compare implementation/infrastructure changes with shared architecture docs
- update architecture only when structure actually changes
- create/propose ADR when rationale matters
- avoid turning architecture docs into changelogs

## P1 — benchmark

Responsibilities:

- pin target versions/revisions
- control environment and warmup
- capture raw metrics + metadata
- compare against baseline without inventing a single misleading winner
- archive reproducible evidence

---

# What should NOT become a skill

Do not create skills for:

- one-line style rules
- secrets policy
- branch protection
- schema validation that a script can enforce
- mandatory test commands that CI can run
- static architecture facts
- historical incident records
- temporary one-off tasks
- project-specific implementation details that belong inside that project

---

# Decision

**Yes, B.I.M.A-DEV-INFRA should have Agent Skills.**

But the repo should treat skills as one layer in an agent-governance stack, not as a magical replacement for rules, tests, or documentation.

Final policy:

```text
GUIDANCE       -> AGENTS.md / path instructions
PROCEDURE      -> Agent Skill
ENFORCEMENT    -> hooks / scripts / CI / GitHub rules
MEMORY         -> architecture / ADR / incidents
EVIDENCE       -> reports / logs / artifacts / test results
```

The next implementation should add only the first two skills (`research-update` and `workflow-audit`) plus deterministic validators they genuinely need. Add later skills when repeated real work proves the procedure deserves one.
