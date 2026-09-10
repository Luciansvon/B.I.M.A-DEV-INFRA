# Architecture plan audit — 2026-09-10

Outcome: **architecture decided through [ADR-0009](../decisions/ADR-0009-capability-verification-architecture.md); new runtime implementation remains staged.**

## Scope and evidence snapshot

Audited issue bodies/comments for [#3](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3), [#8](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/8), [#9](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/9), [#15](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/15), [#17](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/17), plus [RFC-0001](../rfcs/RFC-0001-verification-control-plane.md), shared architecture/contracts, relevant ADRs, source generators, schemas, workflows and incident records. This is a plan/architecture audit, not an exhaustive vulnerability review of every provider repository.

Remote: `https://github.com/Luciansvon/B.I.M.A-DEV-INFRA.git`.
Fetched/pruned `origin`; initial clean local `main` and `origin/main`: `006d782114c9667b8dbe7edaf37601c36667ba43`.

Live issue update timestamps at audit:

| Issue | Last updated UTC | Snapshot state |
|---|---|---|
| #3 | 2026-09-09 16:27:03 | Open, active P1; immediate P0 and consumers complete |
| #8 | 2026-09-09 11:01:55 | Open, parked P3; development gate unmet |
| #9 | 2026-09-09 11:01:52 | Open, blocked P2; preprocessing and benchmark incomplete |
| #15 | 2026-09-09 18:33:24 | Open, unlabelled proposal |
| #17 | 2026-09-10 01:02:44 | Open, unlabelled architecture proposal |

Live GitHub checks showed five open issues, no open PR, an empty rulesets response and no detected repository license. Latest existing [main CI run 34376385578](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34376385578) reports success on `006d782`. That historical run does not validate this documentation change. Detailed hosted test/artifact observations remain in the [consumer validation record](VALIDATION-2026-09-09-AI-COLOR-CONSUMER.md); this audit did not redownload those historical artifacts.

Research: [52 distinct primary sources](../research/SOURCES-ARCHITECTURE-2026-09-10.md), with failed fetches and unverified provider claims separately disclosed. No new providers were installed or benchmarked. No remote issue messages/settings or consumer pins were changed by the architecture decision.

## Findings and disposition

| ID | Priority | Finding and impact | Decision |
|---|---|---|---|
| A01 | P1 | RFC-0001 proposes ReleaseProof first; #15 proposes Graphify before memory; #17 proposes policy then v2. Three orders can cause duplicated work. | One [NEXT](../NEXT.md); contracts and real failure normalization first, experiments independently gated. |
| A02 | P1 | #17's gate is shown only at task entry; a later agent action/provider could appear authorized by association. | Gate every operation and bind authorization to request, subject, trusted policy, scope, approval and budget. Enforce in executor. |
| A03 | P1 | Proposed five-value status combines test outcome, attempt availability and repeated-run instability; skipped/missing results are underspecified. | Separate axes and deterministic precedence; unknown/blocked/flaky required checks cannot publish success. |
| A04 | P1 | v2 proposal omits a migration path, while current canonicalizer/packet readers strictly reject unknown fields/statuses. | Preserve v1; new version/paths, exact mappings, fixture + real consumer migration and rollback proof. |
| A05 | P1 | Deterministic PASS alone does not establish a confirmed root cause or trusted producer. | Require reproduction, scoped regression, causal review and producer/subject provenance before memory promotion. |
| A06 | P1 | Evidence called immutable is currently scratch output plus 14-day artifacts; memory refs can outlive content. | Separate mutable staging and finalized attempt records; retain approved supporting evidence or require revalidation. |
| A07 | P1 | #15 treats Graphify generically as deterministic; upstream describes LLM-based mixed-document extraction. | Pin Graphify-Labs/graphify and benchmark code-only first; semantic mode needs separate cost/data authorization. |
| A08 | P2 | #9's category allocation totals 1,150 despite a 1,000-case minimum. #15's 100-case pilot and #9's model gate are different scopes. | Treat 1,150 as illustrative allocation; preserve >=1,000 total model-benchmark cases and explicit held-out counts, versus >=100 verified fixes for retrieval pilot. |
| A09 | P2 | #9/#15/RFC-0001 still describe the real consumer as pending although #3 and merged evidence record completion. | Mark general consumer proof complete; explicitly require relevant build/test failures for the new triage adapter. |
| A10 | P2 | #9 prefers a model before comparative evidence; #17's linear route implies SLM is mandatory. | No model winner; deterministic/retrieval baseline first and authorized direct strong-agent fallback allowed. |
| A11 | P1 | Optional provider failure, missing evidence, cleanup and cancel behavior lack concrete aggregation rules. | Required work remains non-pass; preserve fallback/omission and cleanup evidence. No retry-induced false green. |
| A12 | P2 | #15's production-source/Windows Daytona claims are not established by the successfully retrieved pages. Several tool names lack immutable identity. | Keep capability optional; do not adopt uncertain source/license/guest-support claims as facts. |
| A13 | P1 | A live SQLite index under this OneDrive checkout would blur local database ownership and replication. | Portable reviewed records plus single-writer rebuildable index outside synchronization/network paths. |
| A14 | P2 | #17's diagram separates verification from later execution and has no obvious ordinary-pass branch; labels can be mistaken for required services. | Execute verifier inside approved runner; publish scoped result directly; implement logical layers as CLI modules. |
| A15 | P1 | #8's provenance and runtime claims can be conflated; signing/package changes can invalidate the tested artifact identity. | Separate proof classes and bind every transformation to digests; test and publish final distributed bytes. |
| A16 | P2 | Current packet `artifact_hash` hashes canonical evidence, not a release binary. New release adapters could misinterpret it. | Preserve v1 meaning and require explicitly named evidence/subject/artifact digests in the next version. |

These priorities describe design risks, not claims of exploitable defects in the current data-only repository audit. Runtime gaps remain pending even though the architecture decisions resolving them are accepted.

## Plan-by-plan verdict

| Plan | Accepted | Revised/deferred | Authoritative role |
|---|---|---|---|
| #3 Cost-aware CI | Machine-first checks, native GitHub, explicit release adapters, measured caching | No universal P1 tool bundle, promised savings, or portability before need; retain unfinished failure normalization | Main implementation tracker using NEXT |
| #8 ReleaseProof | Same-artifact chain, intended installer differences, provenance + behavior, claim evidence | Parked until real use case/reuse/demand gate; no generic first-module mandate | Specialized release verification backlog |
| #9 Local QA | Optional bounded triage, abstention, held-out benchmark, project ownership | Model winner/training undecided; fix corpus arithmetic and consumer scope; no authority from confidence | Gated model experiment |
| #15 Capability map | Provider separation, benchmark/reject gates, lexical baseline | No forced Graphify -> memory dependency; no unsourced provider identity claims | Retained research/catalogue |
| #17 vNext | Capability contracts, policy/budget, evidence, memory invalidation, optional transports/providers | Result axes, repeated gate, migration, enforcement and minimal deployment revised | Input proposal resolved by ADR-0009 |
| RFC-0001 | Project-owned commands, advisory discovery, native evidence and no generic scanner bundle | Historical order/status model superseded; prior text retained under a supersession notice | Historical research, not parallel architecture authority |

## Tool and capability disposition

This table covers every named tool group in the plans. A deferred candidate is not an adoption recommendation. Where only the issue supplies a tool name, resolve owner/repository, license, immutable version and maintained interface before a pilot.

| Candidates | Disposition | Concrete activation/rejection gate |
|---|---|---|
| Task, Python standard-library modules, GitHub Actions, repository audit | KEEP existing baseline | Preserve current commands, pins and fixture/consumer compatibility |
| prek, actionlint, action-validator, pinact, zizmor | KEEP existing scoped checks | Pinact's offline SHA-shape check is not owner/provenance verification; no broad security claim |
| Dependabot; Renovate | KEEP Dependabot; DEFER replacement | Demonstrate grouping/scheduling gap and remove duplicate update automation if migrating |
| poutine, OSV-Scanner/dependency-review, Gitleaks, Trivy, Syft, Grype | OPTIONAL verifier experiments | One actual consumer; compare overlap/false findings/runtime and data freshness; native results retained |
| reviewdog, dorny/test-reporter | OPTIONAL reporting | Choose from a real native test/static-analysis result; never grant report upload authority to execute untrusted source |
| nextest, rust-cache, sccache | PROJECT-SPECIFIC adapters | Rust consumer and measured cold/warm savings; restore/upload cost included |
| autofix.ci | DEFER | Explicit scoped write authorization and deterministic review/verification |
| gh-actions-lockfile, ToolHive | DEFER | Measured integrity/tool-discovery gap beyond current pins/interface requirements |
| Dagger, act, rehearse, Azure Pipelines, GitLab CI | DEFER | Real portability need; hosted authoritative evidence remains required |
| Bazel, Pants, Nix orchestration, MegaLinter, generic self-hosted fleet | DEFER | Project-specific scale/hardware need, isolation and maintenance owner |
| Graphify | EXPERIMENT | Code-only pinned A/B on two repos; source/config miss rate and total agent success/cost |
| SQLite + FTS5/BM25 | SELECTED memory index baseline, NOT BUILT | Reviewed records, local topology, access filters and rebuild/backup proof |
| HelixDB, SurrealDB, embeddings/rerankers | DEFER | Corpus and lexical baseline fail a predeclared requirement; compare total operational burden |
| Corbel, Ballast | REFERENCE CONCEPTS | Resolve upstream identity; adopt reviewed-incident lifecycle concepts without dependency |
| AutoRetrieval | BORROW evaluation loop | Independently validate labels; tune development split, never hidden test oracle |
| Qwen2.5-Coder-1.5B, Granite 4.0 1B, Qwen3.5-0.8B, future small candidates | UNSELECTED model experiments | Verify current exact model identity/license at pilot; >=1,000 verified cases, baseline comparison, target-hardware shadow-mode proof |
| Qwen3.8-labelled community distills | NO default adoption | Unresolved provenance plus same benchmark gate; model names are not quality evidence |
| Daytona; VM/microVM/container/WASM sandbox classes | OPTIONAL execution candidates | Verify workload-compatible isolation, Windows/GUI/reboot if required, costs, evidence export and cleanup |
| DBOS, Restate, Trigger.dev, Temporal | DEFER; default none | Actual durable wait/resume bottleneck; cancellation, retries and external-side-effect idempotency tested |
| Disposable PostgreSQL, Neon, pgbot | PROJECT-OPTIONAL | Real PostgreSQL consumer; local isolated baseline first; Neon current interface still unverified in this pass; pgbot inspect only |
| Tracecat | OPTIONAL external response | Repeated security case need; cannot replace scan/verification authority |
| Plane | OPTIONAL external human interface | GitHub work tracking proves insufficient; evidence links remain authoritative |
| LLVM readobj/size/objdump/pdbutil, Bloaty, cargo-bloat, MSI inspection, diffoscope | SPECIALIZED ReleaseProof adapters | Actual artifact format/question; inspection cannot substitute for installed behavior or producer trust |
| Nub, ScriptC | DEFER toolchain experiments | Resolve exact upstream, lockfile/test parity and measurable value; no core dependency |
| walgit | REFERENCE storage concepts | No change to Git/GitHub or evidence authority based on conceptual similarity |
| PGlite | DEFER embedded DB experiment | A consumer needs PostgreSQL-like embedded semantics; not the failure-memory default |
| Dangerzone | OPTIONAL sanitization concept | Actual untrusted-document ingestion; resolve upstream and test content boundary |
| LangExtract, OpenKB, NexaRAG | REFERENCE / optional extraction | Structured CI evidence stays deterministic; identity/provenance and extraction tests required |
| Syncthing | OPTIONAL snapshot/cache replication | Never sync a live shared SQLite index or use replication as immutable history |
| BYOC/Nuon | DEFER deployment pattern | Actual deployment consumer and ownership/cost/security requirements |
| Tree-sitter, ast-grep, SCIP/LSP indexes | OPTIONAL context adapters | Source navigation/impact claims measured; graph edges do not authorize reduced tests |
| Semgrep, CodeQL, Infer, Clang tooling | PROJECT-OPTIONAL analysis | Actual language/project risk and comparative evidence; not always-on global stack |
| OPA/Conftest | DEFER policy runtime | Repeated policy complexity demonstrably exceeds the small evaluator; migration/security fixtures |
| OpenTelemetry, fleet dashboards | DEFER observability | Multiple consumers need aggregation and retention owner is defined; existing RFC threshold of three consumers retained for fleet UI |
| SARIF, JUnit/native tests, SPDX/CycloneDX, in-toto/SLSA | PRESERVE native formats | Versioned adapter interprets only its supported schema and verified scope |
| GitHub attestations/immutable releases; Cosign | OPTIONAL provenance adapter; DEFER duplicate signing stack | Verify signer/subject/expected workflow; benchmark native path first; publication still explicit |
| MCP | OPTIONAL transport | Metadata is untrusted; policy and executor enforce authorization |

## Delivery decision and limitations

The selected implementation is a small set of reusable CLI modules under existing repository layout. No new service infrastructure or mandatory model runtime. [CAPABILITY-CONTRACT](../architecture/CAPABILITY-CONTRACT.md) fixes operation scope, authorization, result aggregation, native evidence retention, v1 migration and memory/benchmark gates; [NEXT](../NEXT.md) supplies phase exit evidence.

Architecture selection is complete at the document level. Runtime policy enforcement, v2 schema, automated memory, graph retrieval, model inference/training and ReleaseProof are not implemented by this change. Numerical benefit thresholds require a recorded consumer baseline before each experiment. The generic blueprint does not choose a project-specific runner, installer, model or production license.

## Validation for this change

Local Windows validation used Python 3.13.15 on the dirty documentation working tree based on `006d782`. Source code, schemas, tests, workflows, Taskfile and audit policy were not changed.

| Check | Actual result | Retained evidence |
|---|---|---|
| Existing regression suite | 35 discovered: **34 passed, 1 skipped**, no failures; 12.563 seconds | `.artifacts/architecture-2026-09-10/tests.log` |
| Repository audit | **PASS**: 71 files, 137 supported local links, 0 findings | `.artifacts/architecture-2026-09-10/audit/result.json` and `report.md` |
| Canonical evidence | Generated successfully; independent SHA-256 matches checksum file | `.artifacts/architecture-2026-09-10/evidence/` |
| Pass-path packet contract | `not-needed`; zero packet files | `.artifacts/architecture-2026-09-10/agent/` |
| Research ledger | 52 numbered source rows and 52 distinct source URLs | `SOURCES-ARCHITECTURE-2026-09-10.md` |
| Patch whitespace | `git diff --check` clean | Local command output |
| Scope | Documentation-only changes; no runtime/schema/workflow diff | `git diff --name-only` plus untracked-file inventory |

The skipped test is `test_symlink_is_rejected_without_reading_target`: Windows denied symlink creation with WinError 1314. It is not counted as a pass. The canonical digest is `b76ce0e8c4810e83ca5043d64bf4c5927a7f5375e10cf9f03057d92fe1b8a478`; this hash describes the recorded audit result, **not the complete source tree or document bytes**.

Full `task verify` was not run: Task, prek, actionlint, action-validator, pinact and zizmor were absent from this shell's PATH. Their workflow/pre-flight checks are not claimed to pass for this change. Equivalent existing Python regression/audit/evidence/packet commands were run directly, plus patch whitespace review. No tool installation was necessary for this documentation-only decision. No new tests were added to mirror prose.

No hosted validation run, Graphify benchmark, SLM evaluation, installer test or sandbox test was executed for these edits. The output is a verified local documentation change and an accepted architecture specification; implementation gates remain unchecked in NEXT. GitHub issue bodies remain the original proposals until a separately published update.
