# Next implementation and activation steps

Authoritative delivery order: [ADR-0009](decisions/ADR-0009-capability-verification-architecture.md), amended by [ADR-0010](decisions/ADR-0010-verification-aggregate-and-slm-last.md), [ADR-0011](decisions/ADR-0011-artifact-identity-before-release.md) and the 2026-10-28 roadmap-availability amendment in ADR-0010.

This file is a **state board**, not a phase checklist. `task roadmap` enforces the work-availability contract:

- Lane 1 must never be empty; locally completable work is always available.
- A blocked item must name a concrete external gate, a locally completable precursor, and a review date within 90 days.
- A done item must link evidence that exists in the repository.
- Stale review dates fail the build, so a gate cannot be parked indefinitely.

`task roadmap-candidates` derives new work from repository state when Lane 1 starts to empty. The roadmap is intentionally ordered by evidence value, not by phase number.

## Lane 1 — Actionable now

| id | why | state | gate | precursor | verify | evidence | done when | review-by |
|---|---|---|---|---|---|---|---|---|
| P3-02 | The template audit policy is a hand-maintained list that can drift when a scaffold file is added | actionable | - | - | task test | - | Adding a template file without a matching required entry fails the template test | 2027-01-20 |

## Lane 2 — Gated

Each row names the exact external artifact that would unblock it and the local precursor that reduces its risk. A row whose precursor is not actionable, active, or done must be deleted, not parked.

| id | why | state | gate | precursor | verify | evidence | done when | review-by |
|---|---|---|---|---|---|---|---|---|
| P4-20 | Dependency review and trusted-audit adoption need a real manifest-bearing consumer | blocked | consumer: a repository with real manifests and an adopted caller | P4-10 | task test | - | A consumer pull request shows dependency-review and trusted-audit verdicts | 2027-01-20 |
| P4-21 | Cross-repository pin drift needs consumers that actually pin this catalog | blocked | consumer: at least two pinned consumer callers | P4-11 | task pin-freshness | - | Read-only drift report covers real consumer pins without mutating them | 2027-01-20 |
| P4-22 | Artifact identity has contract proof but no real release consumer | blocked | hosted-run: AI-COLOR-COMPARE `main` release using Artifact Identity v1 | P4-09 | task test | - | The release path publishes only after manifest verification and records the verdict | 2027-01-20 |
| P4-23 | Failure memory needs a real corpus and held-out queries before retrieval is meaningful | blocked | corpus: 100 reviewed real records and 10 held-out queries | P4-13 | task contracts | - | The SQLite/FTS5 BM25 benchmark runs on the reviewed corpus and publishes metrics | 2027-01-20 |
| P4-24 | Graphify, ReleaseProof, Spec Kit, sandbox, database, durable, vector, and telemetry providers need measured demand | blocked | provider: two-project reviewed demand and `experiment_gate.py` READY | P4-12 | task test | - | One experiment has a pinned baseline, dataset, thresholds, costs, and rollback | 2027-01-20 |
| P4-25 | The local SLM remains last behind a verified-case and held-out gate | blocked | corpus: 1000 verified cases with a protected held-out split | P4-12 | task contracts | - | Untuned rules and lexical retrieval are benchmarked before any training | 2027-01-20 |

## Done — last 90 days

Rows move here only with committed evidence. Older history stays in Git and in the linked audit records.

| id | why | state | gate | precursor | verify | evidence | done when | review-by |
|---|---|---|---|---|---|---|---|---|
| P2-01 | The workflow contract existed as prose while the catalog checked only input and output names | done | - | - | task catalog | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | Every cataloged workflow documents all required sections and the catalog fails when one is missing or empty | - |
| P3-01 | The project template omitted shipped scaffold files from its own audit policy | done | - | - | task test | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | Deleting a shipped template file fails the generated project audit | - |
| P4-01 | `required_files` omitted the audit verifier and contract docs | done | - | - | task coverage | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | Every automation, schema, workflow, standard, architecture, and catalog path is protected | - |
| P4-02 | The catalog did not require every reusable workflow or input/output to be documented | done | - | - | task catalog | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | Reverse completeness, input/output docs, and consumer proof fail closed | - |
| P4-03 | README, Taskfile, and the command contract disagreed | done | - | - | task test | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | One test compares all three command surfaces and fails on drift | - |
| P4-04 | Trust bundles were only checked during a hosted launch | done | - | - | task trust-bundles | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | Bundle, workflow path, policy hash, and operation id validate locally | - |
| P4-05 | Caller pin pairs and referenced revisions were reviewed by eye | done | - | - | task workflow-refs | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | Mismatched pairs, absent revisions, and missing paths fail locally | - |
| P4-06 | Release evidence had a schema but no validator or field-set parity | done | - | - | task release-evidence | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | A produced document validates and schema fields match the writer | - |
| P4-07 | Schemas had no structural lint beyond top-level field parity | done | - | - | task schema-lint | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | `required`, `$ref`, `pattern`, `const`, and `$defs` are checked | - |
| P4-08 | The project template self-test never audited its scaffold | done | - | - | task test | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | The generated project is committed and passes its own audit | - |
| P4-09 | Release publication did not verify artifact identity before publishing | done | - | - | task test | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | A manifest is verified before publish and a changed byte fails closed | - |
| P4-10 | The trusted audit launcher had no in-repo caller besides its proof job | done | - | - | task test | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | `ci.yml` calls the trusted launcher with the checked-in project policy | - |
| P4-11 | Local caller pins could drift from the reviewed catalog silently | done | - | - | task pin-freshness | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | Local caller pins and catalog hashes are compared read-only | - |
| P4-12 | The experiment gate counted repositories without checking capability identity | done | - | - | task test | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | Demand records name one capability and two distinct reviewed projects | - |
| P4-13 | The failure corpus accepted duplicate or unaudited records toward the 100-case gate | done | - | - | task contracts | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | Duplicate records, fixture evidence posing as real, and self-review fail validation | - |
| P4-14 | Recording the remaining reviewed cases is manual, so the 100-case corpus gate is expensive to approach | done | - | - | task contracts | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | A draft generator emits an unreviewed template with a deterministic ID and refuses to mark it reviewed | - |
| P4-15 | A done row accepted any existing evidence path, even one that never mentions the item | done | - | - | task roadmap | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | Evidence must name the done item ID and an unrelated document fails | - |
| P4-16 | Pin freshness could only inspect this repository, not a local consumer checkout | done | - | - | task test | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | `--consumer-root` compares consumer pins with the catalog and fails on stale or unknown pins | - |
| P4-18 | `required_files` did not protect accepted ADRs or incident guidance | done | - | - | task coverage | docs/audits/VALIDATION-2026-10-29-ROADMAP-GROWTH.md | ADR and incident files are covered and a deleted ADR fails the policy check | - |

## Not roadmap

These are constraints, not tasks. They must not be re-added as checkboxes.

- The 100-record and 10-query failure-memory thresholds are evidence gates; they are not lowered or satisfied with synthetic records.
- The local SLM stays optional and last; it cannot create PASS, authorize retries, or become a required dependency.
- No provider, sandbox, database, durable workflow, vector store, or telemetry installation without two-project demand and a READY experiment decision.
- Spec Kit and domain templates stay parked until they have capability identities, a real consumer, and a gate that can express their prerequisites.
- Generic `build` and `nightly` commands stay absent until a project-agnostic implementation and evidence contract exist.
- Publication, consumer changes, and hosted claims require the separate authorization described in the capability contract.

## Completed baseline

- Capability-based verification architecture, Policy Gate v1, trusted launcher, result normalization v2, verification aggregate v1, artifact identity v1, known-failure registry, failure-memory gates, experiment gate, project template, workflow catalog, dashboard, fleet dispatch, and release template contracts are implemented.
- Hosted proof exists for the audit, launcher, normalization, aggregate, artifact-identity fixture, release template, dashboard, and fleet increments; each claim names its run in the linked audit.
- The previous phase checklist is preserved in Git history before this state-board conversion.
