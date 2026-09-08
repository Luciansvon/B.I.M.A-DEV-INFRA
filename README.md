# B.I.M.A DEV INFRA

Research-backed, reusable GitHub infrastructure for **automation beyond app builds**.

This repository is a laboratory and shared foundation for discovering, validating, and packaging useful GitHub workflows that can be reused across **software, AI/ML, data, research, hardware, publishing, operations, security, education, and future projects that do not exist yet**.

> The repo is intentionally project-agnostic. It should not become tightly coupled to one application, product, language, or device.

## Implementation status

The capability map below describes the research roadmap, not shipped modules. The first executable module is now **experimental repository hygiene**: required-file checks, file-size limits, JSON validation, and a documented subset of local Markdown link checks. It produces JSON/Markdown evidence and has local regression tests.

- [Audit findings and validation status](docs/audits/AUDIT-2026-09-08.md)
- [Run locally or integrate the reusable workflow](docs/standards/REPOSITORY-AUDIT.md)
- [Security and runner baseline](docs/standards/SECURITY-BASELINE.md)
- [Implementation decision](docs/decisions/ADR-0001-executable-repository-hygiene.md)
- [Next steps](docs/NEXT.md)

Hosted workflow execution, protected checks, and a published consumer reference remain pending. A local passing report does not establish CI or production readiness.

## Core idea

GitHub can be treated as more than source control:

```text
EVENT / HUMAN / API / SCHEDULE
            |
            v
         GitHub
   +--------+--------+
   |        |        |
 Issues   Actions   API/Webhooks
   |        |        |
   v        v        v
 PLAN    EXECUTE   INTEGRATE
   |        |        |
   +--------+--------+
            |
            v
       EVIDENCE / RESULT
   +--------+--------+
   |        |        |
 Report   Release   Dashboard
```

The useful mental model is:

**GitHub = versioned source of truth + event system + automation control plane + evidence trail.**

It is *not* automatically the right place for databases, large AI models, long-running servers, or exact-time schedulers.

---

## Research basis

The initial architecture was derived from a **100+ source research pass on 2026-09-08**, prioritizing:

- Reddit communities such as `r/github`, `r/devops`, `r/selfhosted`, `r/homelab`, `r/Terraform`, `r/Playwright`, `r/AskAcademia`, `r/esp32`, and related technical communities.
- Current GitHub documentation and changelogs.
- Real open-source repositories using GitHub for hardware CI, OTA firmware, visual regression, fuzzing, reproducible research, PCB validation, and other non-standard workflows.

Research findings:

- [`docs/research/GITHUB-USE-CASES-2026-09-08.md`](docs/research/GITHUB-USE-CASES-2026-09-08.md)
- [`docs/research/SOURCES-2026-09-08.md`](docs/research/SOURCES-2026-09-08.md)

---

# Capability map

## 1. Software delivery

- CI and regression testing
- build / package / release
- changelog generation
- dependency updates
- compatibility matrices
- API contract validation
- release provenance

## 2. AI / ML

- Model A vs Model B benchmark
- prompt regression tests
- LLM-as-judge evaluation
- latency / RAM / VRAM / throughput tracking
- dataset validation
- model-version comparison
- automatic leaderboard generation
- hardware-specific evaluation through self-hosted runners

Recommended pattern:

```text
GitHub
  |
  v
self-hosted runner
  |
  +-- local model cache
  +-- evaluation dataset
  +-- benchmark engine
  |
  v
result.json / report.md
  |
  v
GitHub artifact / Pages / PR comment
```

Large models should remain in a model store, Hugging Face cache, object storage, or local disk. Do **not** repeatedly commit or upload multi-GB model weights to Git.

## 3. Data automation

- scheduled ETL
- API collection
- web scraping where permitted
- open-data refresh
- CSV/JSON generation
- data-quality checks
- schema validation
- periodic reports
- repository-backed public datasets

## 4. Research and science

- version research code and manuscripts
- reproducible experiment configuration
- generate figures/tables
- compile LaTeX/PDF papers
- preserve experiment history
- publish research websites
- track review tasks through Issues

## 5. Hardware / electronics / IoT

- ESP32 / MCU firmware CI
- OTA firmware deployment
- Hardware-in-the-Loop testing
- serial-device validation
- PCB ERC / DRC
- Gerber / BOM / schematic generation
- board render / visual diff
- signed firmware releases

## 6. Infrastructure / operations

- Infrastructure as Code
- GitOps
- Terraform plan / drift detection
- Ansible execution
- environment promotion
- deployment approvals
- remote lab operation
- cloud-resource provisioning
- secret rotation orchestration

## 7. Quality engineering

- visual regression
- screenshot comparison
- browser E2E
- accessibility / WCAG checks
- Lighthouse performance budgets
- binary-size regression
- performance benchmark regression
- fuzz testing
- API contract testing
- broken-link checking

## 8. Security / compliance

- dependency review
- Dependabot / Renovate workflows
- CodeQL
- secret scanning
- SBOM generation
- artifact attestation
- immutable releases
- OIDC-based cloud authentication
- policy-as-code
- license checks
- workflow hardening

## 9. Publishing / content

- GitHub Pages
- technical documentation
- static websites
- changelogs
- RSS generation
- podcast/feed metadata automation
- scheduled content transforms
- document builds
- portfolio publishing

## 10. Project governance

- Issues as structured work units
- sub-issues
- milestones
- Projects boards / tables / roadmaps
- RFC / ADR review
- Discussions / Q&A / polls
- Issue Forms
- release planning
- evidence attached to decisions

## 11. Repository fleet management

- reusable workflows
- composite actions
- central templates
- mass dependency updates
- standard security gates
- organization-wide conventions
- reusable benchmark pipelines
- centralized release policy

## 12. Monitoring and integration

- scheduled health checks
- status-page generation
- notifications to external systems
- REST / GraphQL automation
- repository webhooks
- GitHub Apps
- `repository_dispatch`
- external event -> GitHub workflow

## 13. Backup / mirroring

- repository mirroring
- GitHub <-> GitLab / Bitbucket sync
- configuration history
- disaster-recovery copies

Git is useful as one layer of recoverability, but GitHub should **not** be treated as the only backup for critical systems.

## 14. Education / automated assessment

GitHub Actions can still implement:

- automated grading
- tests per submission
- assignment templates
- feedback through pull requests
- coding exercises

**Do not build new infrastructure around GitHub Classroom.** GitHub Classroom was decommissioned on **2026-08-28**. Generic repository + Actions based assessment remains possible.

---

# Strongest reusable architecture

```text
                    EVENT
      +---------------+---------------+
      |               |               |
     Git             API          Schedule
      |               |               |
      +---------------+---------------+
                      |
                      v
                GitHub Workflow
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
 GitHub Runner   Self-hosted     External API
                    Runner
       |              |              |
       +--------------+--------------+
                      |
                      v
              Validation / Work
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
    Artifact        Report        Release
       |              |              |
       +--------------+--------------+
                      |
                      v
              Auditable history
```

---

# What belongs here

Reusable infrastructure with value across multiple project types:

```text
.github/
  workflows/
  actions/

templates/
  workflows/
  issues/
  repositories/

benchmarks/
  schemas/
  runners/
  reporters/

automation/
  data/
  research/
  release/
  security/
  hardware/
  monitoring/

docs/
  architecture/
  research/
  decisions/
```

Do not add a workflow merely because automation is possible. Add it when GitHub provides at least one real advantage: **reproducibility, review, event triggering, audit trail, permissions, shared reuse, evidence, or integration**.

---

# What GitHub should NOT become

Avoid using this repository to justify bad architecture.

| Bad fit | Better home |
|---|---|
| Multi-GB AI model weights | Hugging Face / object storage / local model store |
| Production transactional database | PostgreSQL / SQLite / proper DB |
| Exact real-time scheduling | dedicated scheduler / queue / service |
| Long-running stateful service | server / container platform |
| Secrets committed to Git | GitHub Secrets / OIDC / secret manager |
| Sole backup of critical data | independent backup + mirror |
| Untrusted PR on privileged persistent runner | ephemeral isolated runner |
| Huge media archive | object/media storage |

Also avoid workflows that simply add another network hop without improving safety, auditability, reproducibility, or usability.

---

# Current platform notes — 2026-09-08

- **Self-hosted GitHub Actions remain free.** GitHub postponed the previously announced 2026 self-hosted runner platform charge.
- **GitHub Classroom is decommissioned** as of 2026-08-28.
- **GitHub Models is retired** as of 2026-07-30. Do not design AI evaluation around the old GitHub Models inference API.
- Prefer external/local models with GitHub coordinating evaluation.
- For self-hosted runners, prefer isolated or ephemeral execution for risky workloads.

---

# Design principles

1. **Project-agnostic** — reusable outside current projects.
2. **Evidence-first** — workflows should produce logs, reports, artifacts, checks, or measurable results.
3. **Reproducible** — pin versions and record configuration.
4. **Secure by default** — least privilege, OIDC, protected workflows, SHA pinning where appropriate.
5. **Human-controlled production** — risky operations require explicit gates.
6. **Local hardware when hardware matters** — benchmark on the target machine instead of pretending a random cloud runner represents it.
7. **No giant binaries in Git** — store references and results, not unnecessary payloads.
8. **Reusable before duplicated** — central workflow beats twenty nearly identical YAML files breeding in separate repos.
9. **Measure before automate** — automation that cannot prove value is merely faster confusion.

---

# Initial roadmap

### Phase 0 — Research foundation

- [x] 100+ source cross-domain research
- [x] Reddit/community review
- [x] current GitHub capability verification
- [x] anti-pattern mapping
- [x] source ledger

### Phase 1 — Shared workflow foundation

- [x] reusable workflow conventions (documented contract and first experimental implementation)
- [x] security baseline (workflow defaults implemented; repository protection pending)
- [ ] standard artifact/report schema
- [x] workflow versioning strategy (paired full SHA pins; experimental contract)
- [x] runner policy (hosted audit baseline; specialized hardware policies pending)

### Phase 2 — Workflow modules

- [ ] benchmark framework
- [ ] data automation template
- [ ] research/PDF template
- [ ] hardware/HIL template
- [ ] visual regression template
- [ ] security/supply-chain template
- [ ] release template
- [ ] monitoring template

### Phase 3 — Cross-repository infrastructure

- [ ] repository template
- [ ] reusable workflow catalog
- [ ] dashboard / GitHub Pages
- [ ] experiment history
- [ ] organization/repository fleet automation

---

## Research

Start with the research document before adding new infrastructure:

**[`docs/research/GITHUB-USE-CASES-2026-09-08.md`](docs/research/GITHUB-USE-CASES-2026-09-08.md)**

The full retained source ledger is stored in:

**[`docs/research/SOURCES-2026-09-08.md`](docs/research/SOURCES-2026-09-08.md)**
