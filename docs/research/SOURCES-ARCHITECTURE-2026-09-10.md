# Architecture audit source ledger — 2026-09-10

Purpose: decision evidence for [ADR-0009](../decisions/ADR-0009-capability-verification-architecture.md). This is an additional ledger; earlier research remains intact.

Method: reviewed relevant documentation sections, repository READMEs, and paper abstracts through live web retrieval on 2026-09-10. The 52 numbered sources below are distinct successfully retrieved primary sources. They establish documented capabilities and constraints, not measured B.I.M.A performance. Papers were assessed at abstract level; no full-paper replication is claimed. Repository descriptions are upstream claims until tested. Decisions in the last column are this audit's conclusions, not upstream endorsements. No percentage savings or provider benchmark results are inferred from source counts.

## Execution and platform contracts

| ID | Source | Observed support and decision relevance |
|---|---|---|
| S01 | [GitHub reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) | Typed inputs, explicit outputs and immutable refs support shared execution with project configuration; nested permissions cannot increase. |
| S02 | [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use) | Least privilege and untrusted-input handling support isolating subject code from the trusted executor. |
| S03 | [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) | Job permissions are explicit; unspecified permissions become none when a permissions map is supplied. |
| S04 | [Workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) | Named groups and cancellation support bounded native orchestration; choose groups per workflow. |
| S05 | [Artifact download and retention](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts) | Retention is finite/configurable; exported historical cases cannot rely indefinitely on an Actions URL. |
| S06 | [Deployment environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments) | Review, bypass and branch settings are enforcement mechanisms separate from a JSON policy decision. |
| S07 | [Artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations) | Attestations must be verified; generating them alone provides no verification result. |
| S08 | [Immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases) | Release attestation connects tag, commit and assets; retain separate behavior tests. |
| S09 | [Task guide](https://taskfile.dev/docs/guide) | Dependencies can run concurrently; ordered commands are needed for dependent evidence stages. |

## Evidence and authorization

| ID | Source | Observed support and decision relevance |
|---|---|---|
| S10 | [SLSA provenance](https://slsa.dev/spec/v1.2/provenance) | Provenance describes origin and production of an artifact; it is not application acceptance. |
| S11 | [SLSA artifact verification](https://slsa.dev/spec/v1.2/verifying-artifacts) | Verification needs trusted builder identity, signature, subject digest and expected parameters. |
| S12 | [in-toto statement](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md) | Subject digests and predicate types bind claims to artifacts. |
| S13 | [JSON Schema 2020-12](https://json-schema.org/draft/2020-12) | Explicit schema dialect/version supports structural validation; semantic validation is still required. |
| S14 | [RFC 8785](https://www.rfc-editor.org/info/rfc8785/) | Canonicalization defines deterministic JSON representation; do not call the existing bounded serializer full JCS. |
| S15 | [CycloneDX overview](https://cyclonedx.org/specification/overview/) | Component, dependency and completeness information justify preserving native SBOMs. |
| S16 | [SPDX specifications](https://spdx.dev/use/specifications/) | A dedicated structured specification exists; a custom evidence envelope need not replace it. |
| S17 | [OPA policy language](https://www.openpolicyagent.org/docs/policy-language) | Rego evaluates structured policy data; useful alternative if rule duplication later justifies adoption. |
| S18 | [OPA decision logs](https://www.openpolicyagent.org/docs/management-decision-logs) | Decision IDs, input and result provide a reference for traceable policy decisions. |
| S19 | [MCP tools specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) | Tool annotations from untrusted servers cannot establish authority. This is a dated specification reference. |
| S20 | [MCP security practices](https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices) | Token passthrough is an authorization anti-pattern; transport must not grant extra privilege. |

## Memory and evaluation

| ID | Source | Observed support and decision relevance |
|---|---|---|
| S21 | [SQLite use cases](https://www.sqlite.org/whentouse.html) | Single-writer concurrency is a constraint; a local reviewed-case index is an appropriate first topology. |
| S22 | [SQLite FTS5](https://www.sqlite.org/fts5.html) | Built-in BM25 ranking supports a lexical baseline without embeddings; smaller scores rank better. |
| S23 | [SQLite WAL](https://www.sqlite.org/wal.html) | WAL requires same-host coordination and does not work over network filesystems. |
| S24 | [SQLite backup API](https://www.sqlite.org/backup.html) | Consistent snapshots support backup; copying a live database arbitrarily is not the selected export protocol. |
| S25 | [scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html) | Test data must not influence fitting or model selection; applies to retrieval tuning and preprocessing. |
| S26 | [Graphify upstream](https://github.com/Graphify-Labs/graphify) | Code-only extraction is local AST processing; mixed document extraction can use an LLM. Benchmark modes separately. |
| S27 | [AutoRetrieval upstream](https://github.com/daly2211/autoretrieval) | Keep/discard evaluation loop is reusable; model-generated question labels require independent validation. |
| S28 | [pytest flaky tests](https://docs.pytest.org/en/stable/explanation/flaky.html) | Intermittence can reflect uncontrolled state or ordering; retain attempts and classify stability separately. |
| S29 | [BEIR paper](https://arxiv.org/abs/2104.08663) | Abstract reports BM25 as a robust baseline and cost tradeoffs for richer retrieval; does not prove CI-log results. |
| S30 | [CodeRAG-Bench paper](https://arxiv.org/abs/2406.14497) | Abstract reports useful-context retrieval and context integration limitations; measure task success, not graph size. |
| S31 | [Cross-validation guidance](https://scikit-learn.org/stable/modules/cross_validation.html) | Group and time-aware splits motivate separating related incidents and future cases. |

## Optional orchestration and isolation

| ID | Source | Observed support and decision relevance |
|---|---|---|
| S32 | [DBOS documentation](https://docs.dbos.dev/) | Durable programs and queues are available; no current B.I.M.A workload demonstrates a need. |
| S33 | [Restate concepts](https://docs.restate.dev/foundations/key-concepts) | Server, SDK, journal and replay add an operational contract beyond a normal CI job. |
| S34 | [Trigger.dev runs](https://trigger.dev/docs/runs) | Runs contain separate attempts; provider success after retries must not erase B.I.M.A failure history. |
| S35 | [Temporal execution](https://docs.temporal.io/workflow-execution) | Durable replay depends on event history and deterministic commands; defer this operational layer. |
| S36 | [PostgreSQL restore](https://www.postgresql.org/docs/current/app-pgrestore.html) | Restores can execute source-controlled code; database isolation includes dump/migration trust. |
| S37 | [Daytona documentation](https://www.daytona.io/docs/en/) | SDK/API and sandbox interfaces exist; Windows CLI support is not proof of Windows guest or installer behavior. |
| S38 | [Docker security](https://docs.docker.com/engine/security/) | Daemon privilege and configuration matter; a container label alone is not sufficient isolation evidence. |
| S39 | [Windows Sandbox](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/) | Disposable desktop environment; closing it deletes state, so exported results must survive teardown. |
| S40 | [Daytona repository](https://github.com/daytonaio/daytona) | Describes interface/control/compute planes and client packages; does not establish production source availability. |

## Specialized adapters

| ID | Source | Observed support and decision relevance |
|---|---|---|
| S41 | [Tracecat upstream](https://github.com/TracecatHQ/tracecat) | Security workflows/cases, Temporal and deployment components justify an external optional response adapter. |
| S42 | [Plane upstream](https://github.com/makeplane/plane) | Planning/tasks/docs are an external human interface; no need to build them into the verification core. |
| S43 | [HelixDB upstream](https://github.com/helixdb/helix-db) | Graph/vector storage is available, but no measured B.I.M.A corpus need yet justifies it. |
| S44 | [SurrealDB upstream](https://github.com/surrealdb/surrealdb) | Broad database capabilities and component-dependent licensing require version-specific review before a pilot. |
| S45 | [LLVM readobj](https://llvm.org/docs/CommandGuide/llvm-readobj.html) | Headers, sections and format metadata provide bounded inspection evidence. |
| S46 | [LLVM security scope](https://llvm.org/docs/Security.html) | Untrusted-input handling is outside some tooling security guarantees; run risky inspections in appropriate isolation. |
| S47 | [Syft upstream](https://github.com/anchore/syft) | Native SPDX/CycloneDX outputs support SBOM reuse instead of custom inventory formats. |
| S48 | [OSV-Scanner](https://google.github.io/osv-scanner/) | Dependency inventory is matched against OSV vulnerability data; record database freshness when integrating. |
| S49 | [zizmor upstream](https://github.com/zizmorcore/zizmor) | Workflow security analysis remains a scoped static-analysis capability. |
| S50 | [pgbot upstream README](https://github.com/pgrundev/pgbot/blob/main/README.md) | Structured inspection is distinct from optional AI explanation; scope a future adapter to deterministic inspection. |
| S51 | [OASIS SARIF source](https://github.com/oasis-tcs/sarif-spec) | Static-analysis interchange format supports native findings; it is not a universal test/benchmark schema. |
| S52 | [Syncthing FAQ](https://docs.syncthing.net/users/faq.html) | Modification and deletion replicate across devices; replication cannot serve as immutable evidence storage. |

## Unresolved or excluded evidence

- Neon documentation fetches at `neon.com/docs/introduction/branching`, `neon.com/docs/manage/branches`, and the older `neon.tech` address failed in the browser extraction path. Branch-provider capability remains a proposal from #15/#17, not a currently verified integration. Excluded from the 52-source count.
- Initial OASIS HTML and pytest `how-to/flaky.html` fetches failed; S51 and S28 are successfully retrieved alternatives. Initial guessed Dangerzone repository returned 404; no claim about its availability follows from that failure.
- Daytona computer-use page timed out. Windows guest capability, pricing and production code availability were not established; #15's statements are not adopted as facts.
- Names such as Corbel, Ballast, Nub, ScriptC, walgit, OpenKB and NexaRAG in the issue bodies lack immutable owner/repository/version references. Their positions remain reference/deferred until provenance is resolved. No installs or benchmark claims are authorized by these names.
- Community search surfaced AutoRetrieval author posts but these were not used as independent technical evidence or counted. This pass prioritizes primary sources for architecture; community demand validation remains an activation gate for ReleaseProof.
- Existing issue claims of hundreds/thousands of researched sources are not reproduced by this audit. This ledger records only this pass and does not upgrade those historical claims.
