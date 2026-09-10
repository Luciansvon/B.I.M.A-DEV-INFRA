# Next implementation and activation steps

Authoritative delivery order: [ADR-0009](decisions/ADR-0009-capability-verification-architecture.md), accepted 2026-09-10. This is a roadmap; unchecked steps are not implemented.

## Completed baseline

- [x] Immediate #3 P0 sequence: Task, prek, action-validator, pinact, zizmor, canonical evidence and bounded agent packet.
- [x] External fixture with reviewed matching pins and inspected [evidence](audits/VALIDATION-2026-09-09-CONSUMER-FIXTURE.md).
- [x] Real [AI-COLOR-COMPARE consumer](audits/VALIDATION-2026-09-09-AI-COLOR-CONSUMER.md), paired pins and canonical evidence. One consumer supports beta, not broad stable compatibility.
- [x] Audit #3/#8/#9/#15/#17 and RFC-0001; select capability-based architecture and document [contracts](architecture/CAPABILITY-CONTRACT.md). This completes the design decision only.

## 0. Governance activation — owner decisions

- [ ] Select license. No license is chosen implicitly by an architecture decision.
- [x] Activate main protection with solo-maintainer approval count `0`. Require workflow-lint and Ubuntu/Windows checks, strict update, admin enforcement, linear history and conversation resolution; prevent force-push/deletion. API state inspected 2026-09-10.
- [ ] Verify compatibility before repository-level SHA enforcement.

These decisions gate claims of protected/governed publication, not unprivileged local design or validation work. Retain Dagger PR #2 on its existing closed/deferred branch.

## 1. Small executable project and policy contract

- [x] Implement strict versioned JSON project/policy/request/decision schemas and pure deterministic validation.
- [x] Record trusted policy source, exact operation scope, approval reference, obligations and budget; unknown policy fails closed.
- [x] Integrate `repository-audit.v1` with revision/cleanliness checks, output containment, subprocess timeout and decision evidence. No generic provider loader or permanent service.
- [x] Publish hosted Ubuntu/Windows evidence for this increment: run `34442172182`, 49 tests per OS, matching canonical evidence and zero findings. Consumer pins remain unchanged pending real-consumer compatibility proof.
- [ ] Prove malicious declarations cannot elevate permission; prove policy edits in a subject branch cannot authorize that branch.

Exit evidence: bounded positive/negative fixtures, decision report and one enforced operation; documentation alone is not Policy Gate completion.

## 2. Real failure normalization and explicit result migration

- [x] Select AI-COLOR-COMPARE Rust libtest output plus a bounded, sanitized TypeScript diagnostic format from real successful/failed workflow runs.
- [x] Preserve per-attempt outcomes, source/command/policy/environment identity, expected test counts and missing-output semantics in additive local v2 evidence.
- [x] Implement a narrow exact-match known-failure registry with mandatory owner/reviewer, maximum 90-day expiry and explicit `automatic_retry_allowed=false`; DEV-INFRA hosted cross-platform regression passes. Consumer integration remains pending.
- [ ] Complete the additive v2 migration: local adapter, deterministic single-check aggregation and DEV-INFRA hosted cross-platform regression proof exist; hosted consumer PASS/FAIL, consumer opt-in and rollback evidence remain pending. v1 is unchanged.
- [ ] Keep v1 readers/pins working; prove fixture and AI-COLOR-COMPARE migration/rollback with hosted artifacts before updating callers.

Exit evidence: successful and failing real examples, malicious/malformed/missing-result fixtures, equivalent-retry classification and compatibility report. Start verified case collection here.

## 3. Reviewed memory and lexical retrieval

- [ ] Define portable versioned failure records with causal evidence, review, ownership, supersession and invalidation.
- [ ] Implement a rebuildable single-writer SQLite + FTS5 index on local storage outside synchronization folders.
- [ ] Prove import/export, invalidation, access filtering and backup/rebuild on representative records.
- [ ] Collect at least 100 real failure/fix cases for the first meaningful retrieval pilot; preserve a held-out query set and report limitations.

Exit evidence: exact-match + BM25 baseline, recall/false-match/stale-hit metrics and retained verification references. Schema collection does not wait for 100 cases; advanced database adoption does.

## 4. Independent experiments — no mutual dependency

| Experiment | Prerequisite | Required evidence before adoption |
|---|---|---|
| Graphify context | Pinned candidate, measured native-search tasks and allowed data scope | A/B on DEV-INFRA + AI-COLOR-COMPARE; task success, missing edges, total context/time/build cost; code-only first |
| ReleaseProof | #8's competitor/reuse/demand gate and one project-owned release case | Same-artifact provenance + installer behavior; one format and explicit expectations |
| Local QA SLM | Step 2; relevant consumer; >=1,000 verified total benchmark cases with held-out split | Rules/retrieval comparison, unfine-tuned candidates first, calibration, critical errors, total cost and shadow-mode outcomes |

Graphify does not block memory or ReleaseProof. ReleaseProof does not block test normalization or model benchmark data collection. Model runtime/training remains blocked until its prerequisites are met; a single audit consumer is not itself a build-log benchmark corpus. Training is optional after baseline inference demonstrates a need.

## 5. Additional providers only with a measured consumer need

- [ ] Sandbox pilot only after an enforceable execution/cleanup contract and actual workload; compare local/GitHub baseline.
- [ ] Database sandbox/verifier only for a database consumer; disposable local DB before hosted branching.
- [ ] Durable workflow, security-response UI, external project control, graph/vector storage and fleet telemetry only after recorded unmet requirements and comparative cost evidence.

Every experiment declares baseline, dataset/task identity, acceptance thresholds before execution, costs, reject criteria, permissions and rollback/removal. No provider list is an installation plan. See the [audit matrix](audits/ARCHITECTURE-PLAN-AUDIT-2026-09-10.md).
