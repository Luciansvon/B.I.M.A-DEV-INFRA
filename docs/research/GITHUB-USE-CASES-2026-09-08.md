# GitHub Beyond App Builds — Cross-Domain Research

**Date:** 2026-09-08  
**Research corpus:** 130 retained sources  
**Source ledger:** [`SOURCES-2026-09-08.md`](./SOURCES-2026-09-08.md)

## Research question

What can GitHub realistically be used for **beyond storing code and building applications**, without assuming any current project, product, language, device, or business domain?

---

# Executive conclusion

The most useful general model is not:

```text
GitHub = source code + CI build
```

It is:

```text
GitHub
  = versioned source of truth
  + event system
  + review/governance layer
  + automation control plane
  + evidence/audit trail
  + distribution surface
```

GitHub becomes especially useful when a task benefits from one or more of these properties:

1. **Reproducibility** — the exact configuration/code/input version can be identified.
2. **Event triggering** — push, PR, Issue, release, API call, manual dispatch, or schedule can start work.
3. **Review** — changes can be inspected before they become active.
4. **Auditability** — logs, commits, checks, artifacts, approvals, and releases leave evidence.
5. **Permissions** — different actions can be gated by branches, environments, tokens, or reviewers.
6. **Reuse** — workflows/actions/templates can serve many repositories.
7. **Integration** — REST, GraphQL, webhooks, GitHub Apps, Packages, Pages, and external services can connect around the repository.

If none of those benefits matter, adding GitHub Actions often just converts a simple script into YAML with extra steps and a more creative way to fail.

---

# Capability matrix

| Domain | Example use | GitHub role | Typical executor | Fit |
|---|---|---|---|---|
| Software | CI, tests, releases | control + evidence | hosted/self-hosted runner | Excellent |
| AI/ML | model/prompt benchmark | orchestration + history | GPU/self-hosted runner | Excellent |
| Data | ETL, validation, refresh | scheduler + versioning | runner/external compute | Strong |
| Research | reproducible experiments | provenance + publishing | runner/HPC/external | Strong |
| Hardware | firmware/HIL/PCB CI | orchestration + release | physical self-hosted runner | Excellent |
| Infrastructure | Terraform/GitOps | desired-state review | runner/cloud API | Excellent |
| Security | scanning/SBOM/signing | policy + evidence | runner/security service | Excellent |
| QA | visual/accessibility/perf | regression gate | runner/browser farm | Excellent |
| Publishing | docs/static sites/RSS | source + publishing | Actions/Pages | Strong |
| Operations | runbooks/health checks | trigger + audit | self-hosted/external | Strong |
| Community | Issues/Discussions | structured intake | humans + bots | Strong |
| Governance | RFC/ADR/policy | review + history | humans + Actions | Strong |
| Education | autograding | submission + test | runner | Strong* |
| Backup | mirror/version history | secondary copy | runner/external storage | Limited |
| Database | transactional state | wrong abstraction | database | Poor |
| Long-running service | server process | wrong executor | server/container platform | Poor |

`*` Generic repository + Actions autograding remains viable, but GitHub Classroom itself was decommissioned on 2026-08-28. See G032-G035.

---

# 1. Generic automation and runbook execution

GitHub Actions can run work triggered by:

- commits
- pull requests
- Issues
- releases
- schedules
- manual `workflow_dispatch`
- repository/API events
- external webhooks routed into GitHub

This makes GitHub useful as a **versioned runbook executor**, not merely a compiler.

Examples:

- generate a report
- rotate a non-human credential through a secret manager
- validate a remote system
- refresh a static dataset
- package an archive
- run a migration check
- create an Issue when a check fails
- trigger an external job and retain evidence

Evidence: G001-G005, G021-G023, R001, R009.

---

# 2. Self-hosted remote compute

A self-hosted runner turns GitHub into a remote control plane for hardware you own.

```text
GitHub event
    |
    v
workflow
    |
    v
self-hosted runner
    |
    +-- GPU
    +-- camera
    +-- serial port
    +-- FPGA/MCU
    +-- local network
    +-- proprietary software
    |
    v
result + logs + artifact
```

This unlocks workflows impossible or expensive on generic hosted runners:

- GPU benchmarks
- local AI inference
- physical device testing
- hardware-in-the-loop
- software requiring licensed/local tooling
- LAN-only infrastructure validation
- platform-specific performance testing

Main warning: **persistent privileged runners must not blindly execute untrusted pull-request code**. Isolation, ephemeral runners, least privilege, and trusted-event boundaries matter.

Evidence: G006-G007, G040, R002-R003, R010-R012.

---

# 3. AI/ML evaluation laboratory

GitHub is useful around AI even though model inference itself does not need to live on GitHub.

Possible workflow:

```text
model revision
      +
dataset revision
      +
eval-code revision
      |
      v
benchmark matrix
      |
      +--> quality
      +--> latency
      +--> TTFT
      +--> throughput
      +--> RAM/VRAM
      +--> task success
      +--> hallucination/error classes
      |
      v
JSON + Markdown report
      |
      +--> PR comment
      +--> artifact
      +--> leaderboard
      +--> Pages dashboard
```

Use cases:

- Model A vs Model B
- base vs fine-tuned model
- quantization comparison
- prompt regression
- agent/tool-use benchmark
- OCR/vision benchmark
- model upgrade gate
- dataset-version regression
- hardware-specific model selection
- automatic benchmark history

For small/medium projects, Git history + result JSON can work as a lightweight experiment tracker. At larger ML scale, pair GitHub with model/data/experiment systems such as Hugging Face, object storage, DVC/CML, MLflow, or equivalent tools rather than forcing multi-GB artifacts into Git.

Evidence: E024, E027-E028, E032, R017. GitHub Models itself is retired; see G036-G038.

---

# 4. Data engineering and open-data pipelines

GitHub can coordinate small or moderate scheduled data workflows:

```text
schedule/API event
      |
      v
collect
      |
clean
      |
validate
      |
transform
      |
publish JSON/CSV/report
```

Useful for:

- API snapshots
- public dataset refreshes
- price/metadata/index snapshots where collection is permitted
- schema validation
- data-quality gates
- static analytics reports
- reproducible derived datasets
- open-data mirrors

Great Expectations and similar tools can be executed in CI to prevent bad data from being published.

Limitations:

- Actions scheduling is not a hard real-time scheduler.
- large datasets belong in object/data storage, not ordinary Git history.
- scraping must respect site terms, robots/policies, rate limits, copyright, and applicable law.

Evidence: E020-E021, G001-G002.

---

# 5. Reproducible research and science

Git is naturally useful for research because an experiment can be tied to exact versions of:

- code
- configuration
- preprocessing
- manuscript
- figures
- analysis scripts
- environment definition

GitHub Actions can then regenerate:

- plots
- tables
- reports
- PDFs
- supplementary material
- documentation sites

A paper or report becomes less dependent on "whatever happened on someone's laptop six months ago".

Research collaboration through GitHub is also used for manuscript review/versioning, although it remains less comfortable for collaborators unfamiliar with Git.

Evidence: E009, R042.

---

# 6. Hardware and firmware CI

This is one of the strongest non-app use cases found in the research.

Possible firmware lifecycle:

```text
firmware change
      |
compile matrix
      |
static checks
      |
self-hosted physical device
      |
flash
      |
serial/HIL tests
      |
signed firmware artifact
      |
OTA/release
```

Applicable to:

- ESP32
- Arduino-class devices
- embedded Linux
- robotics
- sensors
- IoT fleets
- lab instruments

Potential tests:

- boot success
- sensor readout
- serial protocol
- network join
- OTA rollback
- power-state behavior
- firmware size regression

Evidence: R018, R054, E005-E008.

---

# 7. PCB / electronics design automation

GitHub can also validate **hardware design files**, not just firmware.

KiCad-based workflows can automate:

- ERC
- DRC
- Gerber export
- drill files
- BOM
- schematic PDFs
- board rendering
- fabrication packages
- design-output artifacts

This creates a hardware equivalent of software CI:

```text
PCB change
   |
   +--> ERC
   +--> DRC
   +--> manufacturing outputs
   +--> visual/render outputs
   |
   v
reviewable artifact
```

Evidence: E001-E004.

---

# 8. Visual regression

For UI, document rendering, CAD previews, charts, web pages, or any deterministic visual output:

```text
baseline image
      vs
new image
      |
      v
diff
      |
threshold exceeded?
   /         \
 yes         no
 block      pass
```

Potential projects:

- web UI regression
- design-system component snapshots
- generated report layout
- map/chart rendering
- document-template layout
- dashboard screenshots

Evidence: R030, R036, E013.

---

# 9. Accessibility quality gate

Actions can run accessibility checks as part of a PR rather than leaving accessibility until the end.

Checks may include:

- axe rules
- WCAG-related automated checks
- page-level regressions
- generated reports

Automated accessibility testing cannot prove full accessibility, but it can prevent known violations from repeatedly reappearing.

Evidence: R033.

---

# 10. Performance budgets

GitHub can reject regressions based on measurable thresholds:

- Lighthouse score
- startup time
- binary size
- CPU time
- memory
- bundle size
- API latency
- benchmark throughput

Example:

```text
baseline bundle = 420 KB
PR bundle       = 610 KB
budget          = +10%

=> FAIL
```

This converts performance from a vague preference into a versioned requirement.

Evidence: E018, E033.

---

# 11. Fuzz testing

Fuzzing can run continuously or on PRs to discover malformed-input crashes and parser bugs.

Google OSS-Fuzz/CIFuzz demonstrates this pattern directly in CI.

Useful targets:

- file parsers
- image codecs
- protocol decoders
- compilers
- serialization formats
- libraries handling untrusted data

Evidence: E010-E012.

---

# 12. API contract testing

GitHub can validate that API producers and consumers remain compatible.

Examples:

- validate OpenAPI schema
- generated client compatibility
- response-shape regression
- backward compatibility
- mocked contract tests

This is useful for systems with multiple services or external integrations where a "small" API change can quietly break something six repositories away.

Evidence: R046, R050.

---

# 13. Infrastructure as Code and drift detection

GitHub is a strong home for desired-state infrastructure because changes are reviewable before execution.

```text
IaC change
   |
PR
   |
plan
   |
policy/security
   |
approval
   |
apply
```

A scheduled workflow can also compare expected state against actual infrastructure and create alerts/Issues for drift.

Evidence: R031-R035, R037-R041.

---

# 14. GitOps

Git can serve as the declared desired state for:

- Kubernetes
- Docker Compose fleets
- homelab services
- cloud configuration
- configuration files

A controller or deployment workflow reconciles the runtime environment with the repository.

The strongest pattern is **reviewed desired state**, not merely "GitHub Action SSHes into a server and runs random shell commands".

Evidence: R013, R041.

---

# 15. Supply-chain security

GitHub can act as a policy gate around dependencies and build outputs:

- dependency graph
- dependency review
- vulnerability checks
- secret scanning
- CodeQL
- SBOM generation
- signed artifacts
- artifact provenance/attestation
- immutable releases
- license policy
- OIDC identity to external clouds/signing systems

Community discussion after supply-chain incidents reinforces the importance of auditing and pinning third-party Actions rather than treating Marketplace YAML as magic dust.

Evidence: G008-G012, R014, R019, E016-E017, E036.

---

# 16. Dependency maintenance at repository-fleet scale

For one repository, dependency automation is convenient. Across tens or hundreds, it becomes infrastructure.

Patterns found:

- Dependabot
- Renovate
- grouped updates
- scheduled update windows
- auto-merge after tests
- SHA-pinned Actions with automated update PRs
- centralized reusable workflows

Important lesson from community reports: one-PR-per-dependency can become notification machinery rather than maintenance. Grouping and policy matter.

Evidence: R019-R029.

---

# 17. Release factory

A repository can implement a reproducible release factory:

```text
tag
 |
tests
 |
build once
 |
checksums
 |
SBOM
 |
sign / attest
 |
release notes
 |
publish
```

The preferred supply-chain pattern is **build once, test that artifact, then promote the same artifact**, rather than rebuilding independently for every environment.

Evidence: R015, E015, E029, E031, G011.

---

# 18. Package and container registry

GitHub Packages/GHCR can distribute reusable build outputs such as:

- containers
- npm packages
- NuGet packages
- Maven/Gradle artifacts
- RubyGems

This makes a repository not only the source of a component but also part of its controlled distribution path.

Evidence: G025-G029.

---

# 19. Documentation quality automation

Documentation can be tested like code:

- Markdown lint
- broken links
- generated API docs
- stale references
- examples that compile/run
- spelling/style rules

This is especially valuable for large knowledge bases where dead links quietly multiply because apparently links also enjoy entropy.

Evidence: E019, E030, E034.

---

# 20. Static publishing with GitHub Pages

GitHub Pages + Actions can publish:

- documentation
- research websites
- dashboards
- benchmark leaderboards
- portfolios
- changelogs
- generated reports
- static data explorers
- status pages
- RSS-backed microsites

Pages is strongest when the final output is static or can be generated statically.

Evidence: G024, E026, R045, R047.

---

# 21. RSS/feed generation and lightweight publishing pipelines

GitHub can version source content and regenerate feeds whenever content changes or on a schedule.

Potential uses:

- blog RSS
- podcast metadata/feed generation
- project-release feed
- changelog feed
- research digest

Evidence: R045, R047, R053.

---

# 22. Localization pipelines

Translation systems such as Crowdin/Weblate can synchronize translation resources with GitHub.

Possible flow:

```text
source strings
     |
translation platform
     |
translated resources
     |
PR
     |
validation
```

This makes localization changes reviewable and testable just like code.

Evidence: E014, E022.

---

# 23. Uptime monitoring and status pages

Upptime demonstrates a deliberately unusual architecture: GitHub Actions performs scheduled checks, Issues can represent incidents, and Pages can publish status.

This is useful as a **lightweight** monitoring/status solution where hard real-time guarantees are unnecessary.

It should not replace dedicated observability for critical high-frequency systems.

Evidence: E025-E026.

---

# 24. Issues as structured operational objects

Issues are not limited to software bugs.

They can represent:

- incidents
- experiments
- research questions
- hardware failures
- procurement tasks
- content requests
- audit findings
- policy exceptions
- benchmark regressions
- maintenance work

Sub-issues add hierarchy; labels/fields/milestones add structure.

Evidence: G017-G019.

---

# 25. Projects as portfolio/roadmap layer

GitHub Projects can organize work across repositories using:

- tables
- boards
- roadmaps
- custom fields
- iteration fields
- linked Issues/PRs

This is useful even if the underlying work spans software, hardware, data, research, and operations.

Evidence: G013-G016.

---

# 26. Discussions as community/governance input

Discussions can serve as:

- Q&A
- design discussion
- proposals
- ideation
- polls
- community support

A useful governance pattern is:

```text
Discussion
   |
idea becomes concrete
   |
Issue/RFC
   |
implementation/review
```

Evidence: G020.

---

# 27. Workflow output -> Issue

Automation can turn evidence into work automatically.

Example:

```text
scheduled audit
     |
failure report
     |
create Issue
     |
assign/triage
```

Applications:

- broken dependency
- stale certificate
- failed data-quality check
- benchmark regression
- dead URL
- drift detection
- hardware test failure

Evidence: E023, E035.

---

# 28. Webhooks/API as an event bus

GitHub can participate in larger automation systems through:

- REST
- GraphQL
- repository webhooks
- GitHub Apps
- workflow dispatch
- repository dispatch

This allows GitHub to be one component of a larger system rather than forcing all execution into Actions.

Example:

```text
external service
      |
webhook/API
      |
GitHub workflow / Issue / PR
      |
review + evidence
      |
external executor
```

Evidence: G021-G023.

---

# 29. Repository mirroring and disaster recovery

GitHub repositories can be mirrored to/from other Git hosting services.

Useful reasons:

- migration safety
- multi-forge open-source presence
- independent disaster-recovery copy
- preserving code/config if one provider is unavailable

But GitHub itself should **not** be the only backup for critical assets.

Evidence: R043-R044, R048-R049, R052.

---

# 30. Knowledge base / versioned Markdown

Git works well for text-oriented knowledge because every edit is versioned and reviewable.

Possible content:

- architecture decisions
- research notes
- SOPs
- RFCs
- policies
- experiment notes
- prompt/eval definitions
- documentation

The weakness is user experience for non-technical collaborators. Git should be chosen because versioning/review matters, not because every note deserves a branch strategy.

---

# 31. Lightweight compliance evidence

Because GitHub records:

- who changed what
- commit history
- reviews
- status checks
- approvals
- releases
- workflow logs

it can contribute evidence for internal governance/compliance processes.

This does not magically make a system compliant. It provides **traceability primitives** that a real policy can use.

Evidence: G008-G012, R051.

---

# 32. Policy as code

Policies can be evaluated automatically before changes proceed.

Examples:

- Terraform policy
- allowed licenses
- dependency restrictions
- naming/convention checks
- security thresholds
- deployment rules

OPA/Conftest is one common pattern discussed by practitioners.

Evidence: R051.

---

# 33. Education and automated assessment

Even after GitHub Classroom's retirement, generic repositories + Actions can still implement:

- starter repositories
- assignment templates
- automated unit tests
- score/report generation
- PR-based feedback
- coding challenges

Do not start a new system dependent on Classroom itself. Its decommission date was 2026-08-28.

Evidence: G032-G035.

---

# 34. Open-source governance and crowdsourcing

GitHub's social/review primitives support projects that are not conventional applications:

- public datasets
- documentation collections
- standards/proposals
- design resources
- open hardware
- research collaboration
- curated lists
- translation projects

The repository can become a reviewed contribution system where a pull request is the unit of proposed change.

---

# 35. Experiment tracking, lightweight version

For modest experiments, a repository can store small structured results:

```text
experiments/
  001/
    config.json
    metrics.json
  002/
    config.json
    metrics.json
leaderboard.json
```

The key advantage is that the result can reference exact:

- commit
- model revision
- dataset revision
- environment/config

This becomes less attractive once artifacts and metadata grow enough to justify specialized experiment infrastructure.

Evidence: E024, E027-E028.

---

# 36. Generated dashboards

Actions can aggregate repository or external data into static JSON/HTML and Pages can publish it.

Examples:

- benchmark leaderboard
- dependency health dashboard
- release matrix
- project status
- compatibility table
- open-data explorer
- research result index

No permanent application server is needed if the output can be regenerated periodically.

Evidence: G024, E026.

---

# Novel project possibilities discovered from the combined patterns

These are intentionally **not tied to any existing project**.

| # | Project concept | GitHub role |
|---:|---|---|
| 1 | AI Model Arena | orchestrate local/cloud model evals and publish leaderboard |
| 2 | Prompt Regression Registry | version prompts/evals and block quality regressions |
| 3 | Open Hardware Release Factory | PCB checks + firmware + BOM + signed release |
| 4 | Sensor Fleet OTA Manager | controlled firmware rollout through self-hosted runners |
| 5 | Public Data Observatory | scheduled API collection, validation, static dashboard |
| 6 | Infrastructure Drift Observatory | periodic Terraform drift reports and Issues |
| 7 | API Compatibility Watch | monitor OpenAPI/contract breaking changes |
| 8 | Accessibility Regression Lab | browser testing + axe reports per PR |
| 9 | Visual Regression Archive | screenshot baselines and reviewable diffs |
| 10 | Performance Budget Gate | Lighthouse/binary/runtime regression protection |
| 11 | Dependency Health Observatory | dependency age, CVEs, licenses, update policy |
| 12 | Reproducible Research Factory | data -> analysis -> figures -> paper/site |
| 13 | Research Digest Publisher | scheduled collection -> curated Markdown/RSS/Pages |
| 14 | Open Dataset Registry | version schemas/metadata and publish validated datasets |
| 15 | Documentation Integrity Monitor | links, examples, API docs, stale-reference checks |
| 16 | Lightweight Public Status Service | scheduled checks + incidents + Pages |
| 17 | Repository Fleet Control | central reusable workflows/templates across many repos |
| 18 | Release Provenance Portal | release hashes, SBOM, signatures, attestations |
| 19 | Policy-as-Code Gate | reusable org/repo policy checks |
| 20 | Incident-as-Issue System | automated evidence -> incident Issue -> postmortem |
| 21 | Localization Sync Factory | source strings -> translation platform -> validation PR |
| 22 | Academic Autograding Engine | generic repo/Actions grading without Classroom |
| 23 | Static Feed Factory | content/release data -> RSS/Atom/JSON feed |
| 24 | Remote Device Test Farm | dispatch workflows to physical self-hosted devices |
| 25 | Configuration Disaster-Recovery Mirror | versioned, mirrored service configuration |
| 26 | Compliance Evidence Index | aggregate checks/releases/reviews into audit reports |
| 27 | Benchmark-as-a-Service for Local Hardware | queue standardized tests to known machines |
| 28 | Software/Hardware Compatibility Matrix | matrix tests -> automatically generated compatibility site |
| 29 | Open Standards/RFC Repository | Discussions -> RFC -> review -> versioned decision |
| 30 | Data Quality Gate Service | reusable schema/quality workflow for many datasets |

---

# Architecture patterns worth reusing

## Pattern A — GitHub as control plane

```text
EVENT
  |
GitHub
  |
validated workflow
  |
external/local executor
  |
result
  |
GitHub evidence
```

Best when execution is expensive, hardware-specific, or outside GitHub.

## Pattern B — GitHub as reviewed desired state

```text
proposed config
   |
PR
   |
plan/check
   |
approval
   |
reconciliation/deploy
```

Best for infrastructure, policy, configuration, and release state.

## Pattern C — GitHub as reproducibility ledger

```text
input version
 + code version
 + config version
      |
experiment
      |
result metadata
      |
commit/artifact/report
```

Best for AI/ML, research, benchmarks, and data.

## Pattern D — GitHub as public publishing pipeline

```text
source/data
   |
Actions transform
   |
static output
   |
Pages/feed/release
```

Best for docs, reports, leaderboards, public data, status, RSS.

## Pattern E — Evidence creates work

```text
automated check
      |
problem found
      |
Issue created
      |
triage
      |
fix / close
```

Best for drift, monitoring, dependency, quality, and security tasks.

---

# Anti-patterns and hard limits

## Do not use ordinary Git as a warehouse for giant binary/model files

Better:

- Hugging Face/model registry
- object storage
- package/container registry
- local model cache

Store references, hashes, manifests, and benchmark results in Git.

## Do not use Git as a transactional production database

Git commits are not row-level transactions, query planning, locking, or a sane substitute for a database.

## Do not rely on Actions cron for exact-time guarantees

Scheduled workflows are suitable for periodic jobs, not hard real-time scheduling.

## Do not use a persistent privileged self-hosted runner for arbitrary untrusted code

Use trusted event boundaries, isolation, ephemeral runners, or dedicated restricted machines.

## Do not treat GitHub as the only backup

Mirrors/version history help recoverability, but critical data still needs an independent backup strategy.

## Do not hide a long-running stateful server inside CI

Actions jobs are jobs. A server should live on infrastructure designed to be a server.

## Do not expose secrets in the repository

Prefer GitHub Secrets, external secret managers, and short-lived OIDC credentials.

## Do not install random third-party Actions without review

Prefer trusted sources, pinning, minimal permissions, and automated update policy. Supply-chain incidents make this a real attack surface, not theoretical ceremony.

## Do not automate merely because a YAML file exists

A useful automation should improve at least one of:

- safety
- repeatability
- evidence
- speed
- consistency
- reviewability
- cost
- integration

Otherwise a local script may be the cleaner system.

---

# Current platform corrections — 2026-09-08

## Self-hosted Actions pricing

The previously announced 2026 platform charge for self-hosted GitHub Actions was **postponed**. Current GitHub billing documentation states that self-hosted runner usage remains free. See G030-G031.

## GitHub Classroom

GitHub Classroom was decommissioned on **2026-08-28**. Generic repository/Actions-based autograding remains technically possible, but new infrastructure should not depend on Classroom. See G032-G035.

## GitHub Models

GitHub Models was fully retired on **2026-07-30**. New AI evaluation infrastructure should use external/local model runtimes while GitHub handles orchestration, versioning, evidence, and reporting. See G036-G038.

## GitHub Spark on github.com

GitHub announced deprecation of Spark on github.com in August 2026, with access changes during August. This research therefore does not make Spark a foundation dependency. See G039.

---

# What B.I.M.A-DEV-INFRA should become

This repository should **not** become a pile of workflows for whichever project happens to exist today.

It should become a reusable infrastructure catalog:

```text
B.I.M.A-DEV-INFRA/
|
+-- workflows/
|   +-- security/
|   +-- release/
|   +-- benchmark/
|   +-- data/
|   +-- research/
|   +-- hardware/
|   +-- quality/
|   +-- monitoring/
|
+-- templates/
|   +-- repository/
|   +-- issues/
|   +-- workflows/
|
+-- schemas/
|   +-- benchmark-result.schema.json
|   +-- automation-report.schema.json
|
+-- docs/
    +-- architecture/
    +-- decisions/
    +-- research/
```

A workflow should graduate into this repository only when it is:

1. useful in more than one plausible domain/project,
2. parameterized instead of hard-coded,
3. documented with inputs/outputs,
4. security-reviewed,
5. testable,
6. versioned,
7. able to produce evidence of what it did.

---

# Recommended implementation order

## Foundation

1. workflow conventions
2. permission/security baseline
3. reusable workflow versioning
4. common artifact/report schema
5. self-hosted runner trust policy

## First reusable modules

1. **security baseline**
2. **release + provenance**
3. **generic benchmark runner**
4. **data quality / scheduled data job**
5. **visual/performance regression**
6. **hardware/self-hosted test template**
7. **monitor -> Issue pattern**
8. **static report -> Pages pattern**

This order creates primitives that can support future projects instead of guessing what the next project will be.

---

# Bottom line

The research does **not** support treating GitHub as a universal backend.

It strongly supports treating GitHub as a **universal coordination and evidence layer** whenever the work is versionable, triggerable, reviewable, and produces a finite result.

That distinction is what keeps this repository reusable instead of turning it into an elaborate YAML-shaped hammer looking for nails.
