# Spec Kit adapter source ledger — 2026-09-13

Purpose: current evidence for the optional Spec Kit adapter audit. This ledger is additive and does not replace earlier research ledgers.

Method: reviewed upstream documentation, source, release metadata, issue discussions, software-supply-chain guidance, and research abstracts through live retrieval on 2026-09-13. The stable upstream snapshot is Spec Kit `v1.0.6`, published 2026-09-10, whose tag resolves to commit `96c9bd657bfd5de0d651a6165084932b7304ac99`. Spec Kit files below are pinned to that commit unless the source is explicitly a live release or issue page. Research papers were assessed at abstract level; no full-paper replication is claimed. Community submissions are experience reports, not independent security or effectiveness proof. No source count is treated as benchmark evidence.

## Upstream product and lifecycle

| ID | Source | Observed support and decision relevance |
|---|---|---|
| S01 | [Spec Kit v1.0.6 release](https://github.com/github/spec-kit/releases/tag/v1.0.6) | Current stable release used for this audit; pin an exact release and resolved commit in any pilot. |
| S02 | [README](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/README.md) | Defines Spec-Driven Development as the product purpose; it is an authoring workflow, not verification authority. |
| S03 | [Changelog](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/CHANGELOG.md) | Six stable 1.0.x releases landed between 2026-08-21 and 2026-09-10; upgrade churn must be measured. |
| S04 | [Security policy](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/SECURITY.md) | Provides coordinated-disclosure routing, not a certification of every catalog component. |
| S05 | [Python package metadata](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/pyproject.toml) | Requires Python 3.11+ and multiple runtime dependencies; it cannot become framework-neutral DEV-INFRA core. |
| S06 | [Documentation index](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/index.md) | Presents integrations, presets, extensions, workflows, and bundles as composable layers. |
| S07 | [Quick start](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/quickstart.md) | Initialization creates project-local assets; future consumers must opt in explicitly. |
| S08 | [Installation guide](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/installation.md) | Installation changes the local tool environment and project scaffolding; audit and rollback are required. |
| S09 | [Upgrade guide](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/upgrade.md) | Managed-file hashes protect edits, while `--force` can overwrite; forbid force in an automated B.I.M.A path. |
| S10 | [Air-gapped installation](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/install/air-gapped.md) | Supports bounded offline operation, useful for a pinned pilot and reproducible cache. |
| S11 | [Existing-project guide](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/guides/existing-projects.md) | Brownfield adoption has explicit setup cost; do not silently initialize existing projects. |
| S12 | [Monorepo guide](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/guides/monorepo.md) | Project boundaries affect feature/spec placement; shared infrastructure must not infer a consumer module graph. |
| S13 | [Evolving-specs guide](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/guides/evolving-specs.md) | Specifications can change after creation; evidence needs revision identity and drift detection. |
| S14 | [SDD concept](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/concepts/sdd.md) | Supports intent-first authoring, but does not make generated implementation correct. |
| S15 | [Complex-features concept](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/concepts/complex-features.md) | Larger work may be decomposed; B.I.M.A still needs deterministic coverage and result evidence. |
| S16 | [Specification persistence](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/concepts/spec-persistence.md) | Persistent artifacts enable review, while stale artifacts remain a measurable risk. |
| S17 | [Spec of specs](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/concepts/spec-of-specs.md) | Describes higher-order specification structure; avoid creating a second authority over B.I.M.A contracts. |
| S18 | [Reference overview](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/reference/overview.md) | Official lifecycle includes constitution, specify, clarify, plan, checklist, tasks, analyze, implement, and converge. |

## Composition, integrations, and execution surface

| ID | Source | Observed support and decision relevance |
|---|---|---|
| S19 | [Core CLI reference](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/reference/core.md) | Non-interactive defaults and initialization behavior must be overridden explicitly in a reproducible pilot. |
| S20 | [Integrations reference](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/reference/integrations.md) | One integration is active by default; Codex installs skills under `.agents/skills`. |
| S21 | [Codex integration source](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/src/specify_cli/integrations/codex/__init__.py) | Codex dispatch can call `codex exec`; this is consequential execution, not passive documentation. |
| S22 | [Extensions reference](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/reference/extensions.md) | Maintainers state community extensions are not reviewed, audited, endorsed, or supported by Spec Kit. |
| S23 | [Presets reference](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/reference/presets.md) | Presets are the intended layer for organization standards and support replace/prepend/append/wrap composition. |
| S24 | [Preset architecture](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/presets/ARCHITECTURE.md) | Resolution order and priority determine the effective artifact; evidence must preserve the full composition chain. |
| S25 | [Preset publishing](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/presets/PUBLISHING.md) | Catalog publication is distribution metadata, not independent behavioral/security proof. |
| S26 | [Artifacts reference](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/reference/artifacts.md) | Read-only artifact introspection can support a bounded adapter without running an agent. |
| S27 | [Workflows reference](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/reference/workflows.md) | Workflows may run prompts, shell steps, loops, fan-out, and human gates; they require separate Policy Gate authorization. |
| S28 | [Bundles reference](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/reference/bundles.md) | Bundles track provenance and pins, but install-time idempotency can skip already-present components without version comparison. |
| S29 | [Authentication reference](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/reference/authentication.md) | Private catalog authentication adds credential scope and must remain outside an initial no-secret pilot. |
| S30 | [Bounded download/extraction source](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/src/specify_cli/_download_security.py) | Upstream bounds downloads and archive extraction; B.I.M.A must still pin and verify obtained bytes. |
| S31 | [Extension development guide](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/extensions/EXTENSION-DEVELOPMENT-GUIDE.md) | Extensions can add commands/hooks/scripts, making them a broader and riskier first layer than a data-only preset. |
| S32 | [Extension API reference](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/extensions/EXTENSION-API-REFERENCE.md) | Hook/event interfaces expand behavior; defer until a measured requirement cannot be met by preset plus validator. |
| S33 | [Agent-context extension](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/extensions/agent-context/README.md) | Context synchronization can target `AGENTS.md`; B.I.M.A must not permit generated content to overwrite repo authority. |
| S34 | [Constitution-sync preset](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/presets/constitution-sync/README.md) | Upstream recommends runtime composition for organization governance and warns that materialized copies drift or are clobbered. |
| S35 | [Constitution-sync manifest](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/presets/constitution-sync/preset.yml) | The bundled sync behavior is opt-in and uses wrap composition; it is not a default governance guarantee. |

## Agentic artifact chain

| ID | Source | Observed support and decision relevance |
|---|---|---|
| S36 | [Agentic SDD reference](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/reference/agentic-sdd.md) | Defines the intended ordered process; B.I.M.A evidence should record which optional stages actually ran. |
| S37 | [Constitution command](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/templates/commands/constitution.md) | Generates governance text through an agent; it cannot authoritatively rewrite B.I.M.A governance. |
| S38 | [Specify command](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/templates/commands/specify.md) | Produces a feature specification; acceptance still requires project-owner review. |
| S39 | [Clarify command](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/templates/commands/clarify.md) | Explicit ambiguity reduction is a plausible benefit to benchmark, not an assumed benefit. |
| S40 | [Plan command](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/templates/commands/plan.md) | Planning reads constitution and specs; it does not grant execution permission. |
| S41 | [Checklist command](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/templates/commands/checklist.md) | Checklists are generated review aids, not deterministic test results. |
| S42 | [Tasks command](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/templates/commands/tasks.md) | Task decomposition can expose missing work; traceability must be validated against actual changes. |
| S43 | [Analyze command](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/templates/commands/analyze.md) | Cross-artifact analysis is agentic and read-only; its findings need declared coverage and cannot replace CI. |
| S44 | [Implement command](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/templates/commands/implement.md) | Implementation is a consequential agent operation and remains outside the first adapter. |
| S45 | [Converge command](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/templates/commands/converge.md) | Iterative convergence may increase cost; benchmark total attempts, time, and tokens. |
| S46 | [Agentic bug-fix reference](https://github.com/github/spec-kit/blob/96c9bd657bfd5de0d651a6165084932b7304ac99/docs/reference/agentic-bugfix.md) | Bug workflow exists separately from feature SDD; do not force every change through a full feature path. |

## Community evidence and unresolved gaps

| ID | Source | Observed support and decision relevance |
|---|---|---|
| S47 | [Governance preset proposal #2362](https://github.com/github/spec-kit/issues/2362) | A maintainer confirms presets are the intended optional governance layer; reported adoption is author-supplied. |
| S48 | [Maintainer preset guidance](https://github.com/github/spec-kit/issues/2362#issuecomment-4316705963) | Supports a B.I.M.A-owned preset instead of changes to Spec Kit core. |
| S49 | [Spec Kit constitution dogfooding gap #2698](https://github.com/github/spec-kit/issues/2698) | Upstream's own constitution adoption remains an open/stale proposal, limiting maturity claims. |
| S50 | [Constitution context-growth bug #4431](https://github.com/github/spec-kit/issues/4431) | Shows temporary review material can accumulate when lifecycle instructions are misunderstood. |
| S51 | [Clarification fix PR #4432](https://github.com/github/spec-kit/pull/4432) | v1.0.6 clarified that Sync Impact Reports are temporary review material. |
| S52 | [Closed-vocabulary analysis proposal #4106](https://github.com/github/spec-kit/issues/4106) | Community measurement found prompt-based checks need coverage reporting and model-level validation. |
| S53 | [Architecture Guard submission #4219](https://github.com/github/spec-kit/issues/4219) | Catalog submission reports one-project testing; it is insufficient evidence for a B.I.M.A global dependency. |
| S54 | [Approval-gates proposal PR #2010](https://github.com/github/spec-kit/pull/2010) | Upstream approval mechanisms are evolving; B.I.M.A Policy Gate remains the authority. |

## Independent standards and platform controls

| ID | Source | Observed support and decision relevance |
|---|---|---|
| S55 | [GitHub reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) | Typed inputs, outputs, immutable refs, and permission non-escalation support a shared validator. |
| S56 | [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use) | Least privilege and untrusted-input handling apply to any future adapter workflow. |
| S57 | [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) | Explicit permissions make unspecified scopes none and keep an audit workflow read-only. |
| S58 | [GitHub Actions security concepts](https://docs.github.com/en/actions/concepts/security) | Script injection, compromised runners, tokens, OIDC, and attestations remain separate risks. |
| S59 | [GitHub artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations) | Provenance can bind packaged adapter bytes; it does not prove spec quality. |
| S60 | [GitHub OIDC reference](https://docs.github.com/en/actions/reference/security/oidc) | Trusted workflow identity can be bound to `job_workflow_ref` and `job_workflow_sha` if credentials are later needed. |
| S61 | [NIST SSDF](https://csrc.nist.gov/projects/ssdf) | Security requirements and design decisions should be tracked, but SSDF is outcome-oriented rather than one mandated tool. |
| S62 | [NIST DevSecOps reference model](https://pages.nist.gov/nccoe-devsecops/notational-reference-model.html) | Security requirements and evidence-based verification belong in the lifecycle, not only in generated prose. |
| S63 | [SLSA provenance v1.2](https://slsa.dev/spec/v1.2/provenance) | Provenance describes where/how an artifact was produced; it is not behavioral acceptance. |
| S64 | [SLSA artifact verification v1.2](https://slsa.dev/spec/v1.2/verifying-artifacts) | Verification requires expected identity and parameters, supporting digest-pinned adapter inputs. |
| S65 | [OpenSSF OSPS Baseline](https://baseline.openssf.org/) | Baseline controls favor automated, evidence-producing project practices; applicability remains risk-based. |
| S66 | [in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md) | Subject digests and predicate identity are reusable for adapter evidence design. |

## Research evidence

| ID | Source | Observed support and decision relevance |
|---|---|---|
| S67 | [Using LLMs in Software Requirements Specifications](https://ieeexplore.ieee.org/document/10628461/) | Empirical results support potential drafting/time benefits, not autonomous correctness or B.I.M.A-specific gains. |
| S68 | [Leveraging LLMs for the Quality Assurance of Software Requirements](https://ieeexplore.ieee.org/document/10628462/) | Supports assisted requirements review; human evaluation remains part of the evidence. |
| S69 | [Aligning Requirement for LLM Code Generation](https://arxiv.org/abs/2509.01313) | Reports specification-perception misalignment and measured gains from an alignment technique; motivates task-level comparison. |
| S70 | [Understanding Specification-Driven Code Generation with LLMs](https://arxiv.org/abs/2601.03878) | Proposes measuring pass rate, time-to-pass, and intervention behavior; results are not yet established by the study design alone. |
| S71 | [Specification-Driven Development for AI-Native Engineering](https://arxiv.org/abs/2607.16680) | Argues for specification governance; its framework and reported literature synthesis do not validate Spec Kit specifically. |
| S72 | [SpecGen](https://arxiv.org/abs/2401.08807) | Formal-spec generation improves when generated candidates are verified; reinforces deterministic verification after authoring. |
| S73 | [ReqInOne](https://ieeexplore.ieee.org/document/11190373/) | Modular SRS generation reportedly improves structure/accuracy; applicability to repository workflows requires a local benchmark. |
| S74 | [LLM-assisted code review empirical study](https://ieeexplore.ieee.org/document/11323409/) | Reports value and false-positive/context concerns; supports hybrid reviewer control rather than autonomous approval. |

## Audit limits

- `74` distinct source URLs were retained; `54` are upstream Spec Kit release, file, issue, or pull-request sources and `20` are platform, standards, or research sources.
- No Spec Kit command, preset, extension, bundle, or consumer installation was run. Source inspection does not establish runtime compatibility with B.I.M.A projects.
- No community catalog artifact was treated as security-reviewed merely because it is listed upstream.
- No paper's reported result was transferred to B.I.M.A as an expected percentage improvement.
- The stable tag was inspected because upstream `main` moved after `v1.0.6`; a future pilot must re-audit its exact pinned version.
