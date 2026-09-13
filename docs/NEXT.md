# Next implementation and activation steps

Authoritative delivery order: [ADR-0009](decisions/ADR-0009-capability-verification-architecture.md), updated by [ADR-0010](decisions/ADR-0010-verification-aggregate-and-slm-last.md). Status refreshed 2026-09-13 against `origin/main` at `bb5a7f7072e5294557798813081544aee492ddfc` before the aggregate-verification increment.

## Completed baseline

- [x] Immediate #3 P0 sequence: Task, prek, action-validator, pinact, zizmor, canonical evidence and bounded agent packet.
- [x] External fixture with reviewed matching pins and inspected [evidence](audits/VALIDATION-2026-09-09-CONSUMER-FIXTURE.md).
- [x] Historical [AI-COLOR-COMPARE consumer](audits/VALIDATION-2026-09-09-AI-COLOR-CONSUMER.md), paired v1 pins and canonical evidence. The proposed v2 migration is closed without a consumer change.
- [x] Audit #3/#8/#9/#15/#17 and RFC-0001; select capability-based architecture and document [contracts](architecture/CAPABILITY-CONTRACT.md). This completes the design decision only.

## 0. Governance activation — owner decisions

- [x] Select Apache-2.0 for permissive cross-project reuse with an explicit patent grant and change-notice obligations.
- [x] Activate main protection with solo-maintainer approval count `0`. Require workflow-lint and Ubuntu/Windows checks, strict update, admin enforcement, linear history and conversation resolution; prevent force-push/deletion. API state inspected 2026-09-10.
- [x] Verify compatibility and activate repository-level SHA enforcement. Live Actions permissions reported `sha_pinning_required=true` on 2026-09-12; pinact 4.1.1 passes all current workflows/actions.

These decisions gate claims of protected/governed publication, not unprivileged local design or validation work. Retain Dagger PR #2 on its existing closed/deferred branch.

## 1. Small executable project and policy contract

- [x] Implement strict versioned JSON project/policy/request/decision schemas and pure deterministic validation.
- [x] Record trusted policy source, exact operation scope, approval reference, obligations and budget; unknown policy fails closed.
- [x] Integrate `repository-audit.v1` with revision/cleanliness checks, output containment, subprocess timeout and decision evidence. No generic provider loader or permanent service.
- [x] Publish hosted Ubuntu/Windows evidence for this increment: run `34442172182`, 49 tests per OS, matching canonical evidence and zero findings. Consumer pins remain unchanged pending real-consumer compatibility proof.
- [x] Implement a trusted reusable launcher that binds separate subject/infra checkouts, exact called-workflow SHA, trusted policy bundle/hash and runner identity.
- [x] Prove locally that subject policy shadowing, scope elevation, workflow-ref substitution, committed policy tampering, repository spoofing and overlapping checkouts fail closed.
- [x] Publish hosted proof for the new trusted launcher workflow: run `34707376819` returned launcher/policy `ALLOW`, launched the verifier and produced a passing 144-file audit. Run `34707376740` separately passed workflow lint plus the Ubuntu/Windows matrix. No consumer pin changed.

Exit evidence: bounded positive/negative fixtures, decision report and one enforced operation; documentation alone is not Policy Gate completion.

## 2. Real failure normalization and explicit result migration

- [x] Select AI-COLOR-COMPARE Rust libtest output plus a bounded, sanitized TypeScript diagnostic format from real successful/failed workflow runs.
- [x] Preserve per-attempt outcomes, source/command/policy/environment identity, expected test counts and missing-output semantics in additive local v2 evidence.
- [x] Implement a narrow exact-match known-failure registry with mandatory owner/reviewer, maximum 90-day expiry and explicit `automatic_retry_allowed=false`; DEV-INFRA hosted cross-platform regression passes. Consumer integration remains pending.
- [x] Validate the additive v2 adapter/action in DEV-INFRA hosted run `34470140936`: Ubuntu and Windows both returned `PASS`, `ALL_EXPECTED_TESTS_PASSED`, `29/29`, at the same source and policy hashes.
- [x] Close AI-COLOR v2 migration without a consumer change. Keep v1 readers and pins active; no opt-in/rollback exercise is required unless a future consumer need reopens migration.
- [x] Implement additive `bima-verification-plan.v1` and `bima-verification-aggregate.v1` contracts with deterministic `FAIL > BLOCKED > UNKNOWN > PASS` precedence, missing-result detection, flaky protection, and visible optional non-pass results.
- [x] Publish and inspect hosted Ubuntu/Windows aggregate artifacts in run `34753773782`. Both report `PASS`, `ALL_REQUIRED_CHECKS_PASSED`, required `1/1`, and no unresolved required check. No consumer pin changed.

Exit evidence: successful and failing real examples, malicious/malformed/missing-result fixtures, equivalent-retry classification and compatibility report. Start verified case collection here.

## 3. Reviewed memory and lexical retrieval

- [x] Define portable versioned failure records with causal evidence, review, ownership, supersession and invalidation.
- [x] Implement a rebuildable single-writer SQLite + FTS5 index gated to local storage outside repositories, synchronization folders and network paths.
- [x] Prove canonical import/export, invalidation exclusion, access filtering and integrity-checked backup/rebuild with synthetic contract fixtures.
- [x] Implement a held-out lexical benchmark gate with deterministic recall@k, MRR, false-match and stale-hit metrics.
- [ ] Collect at least 100 real failure/fix cases for the first meaningful retrieval pilot; 6 independently reviewed shared-infrastructure cases are canonical, while the held-out query set remains empty.
- [ ] Run and publish the production retrieval benchmark after both the 100-real-case and 10-held-out-query gates are satisfied.

Current activation: `BLOCKED`, `6/100` real reviewed cases and `0/10` held-out queries. No database is created below the gate.

History audit: [five technically eligible candidates](audits/FAILURE-MEMORY-HISTORY-AUDIT-2026-09-13.md) were independently reviewed by Bima in PR #27 and converted to canonical active records. A sixth shared-workflow failure from that activation was independently reviewed in PR #28 and converted separately. The corpus is `6/100`; held-out queries remain `0/10`.

Exit evidence: exact-match + BM25 baseline, recall/false-match/stale-hit metrics and retained verification references. Schema collection does not wait for 100 cases; advanced database adoption does.

## 4. Independent experiments — no mutual dependency

| Experiment | Prerequisite | Required evidence before adoption |
|---|---|---|
| Graphify context | Pinned candidate, measured native-search tasks and allowed data scope | A/B on DEV-INFRA + AI-COLOR-COMPARE; task success, missing edges, total context/time/build cost; code-only first |
| ReleaseProof | #8's competitor/reuse/demand gate and one project-owned release case | Same-artifact provenance + installer behavior; one format and explicit expectations |
| Spec Kit authoring adapter | Two distinct reviewed project demands, pinned stable release, native baseline tasks and approved thresholds | Read-only artifact/composition validator first; paired traceability, missing-artifact, acceptance, false-block, security, time/token and upgrade evidence; per-project opt-in only |

Graphify does not block memory or ReleaseProof. ReleaseProof does not block test normalization. Model runtime/training is moved to the final roadmap stage; a single audit consumer is not itself a build-log benchmark corpus.

- [x] Implement a deterministic experiment request/decision gate with pinned baseline, dataset identity, thresholds, budget, permissions, reject criteria, rollback and reviewed demand evidence.
- [x] Require at least two distinct reviewed project repositories for `READY`.
- [ ] Run any experiment. None is currently authorized or active.

Spec Kit was audited against stable `v1.0.6` in the [adapter architecture audit](audits/SPEC-KIT-ADAPTER-AUDIT-2026-09-13.md) using a [74-source ledger](research/SOURCES-SPEC-KIT-ADAPTER-2026-09-13.md). It remains a provider-neutral authoring candidate: no package, preset, workflow, adapter or consumer is installed. B.I.M.A governance, Policy Gate, reviewed verifiers and canonical evidence remain authoritative.

## 5. Additional providers only with a measured consumer need

- [ ] Sandbox pilot only after an enforceable execution/cleanup contract and actual workload; compare local/GitHub baseline.
- [ ] Database sandbox/verifier only for a database consumer; disposable local DB before hosted branching.
- [ ] Durable workflow, security-response UI, external project control, graph/vector storage and fleet telemetry only after recorded unmet requirements and comparative cost evidence.

All provider categories are represented by the experiment-readiness contract. That is a gate implementation, not provider installation or activation.

Every experiment declares baseline, dataset/task identity, acceptance thresholds before execution, costs, reject criteria, permissions and rollback/removal. No provider list is an installation plan. See the [audit matrix](audits/ARCHITECTURE-PLAN-AUDIT-2026-09-10.md).

## 6. Final optional stage — local SLM

- [x] Encode the minimum `1,000` verified-case readiness threshold in the
  deterministic experiment gate. This is a blocker contract, not SLM
  implementation or activation.
- [ ] Reconsider a local QA SLM only after the deterministic control plane,
  useful non-model adapters, Failure Memory baseline, and relevant consumer
  evidence are mature.
- [ ] Retain the minimum gate: deterministic preprocessing, a real relevant
  consumer, and at least 1,000 verified benchmark cases with a protected
  held-out split.
- [ ] Benchmark rules plus lexical retrieval against untuned candidate models
  before any training. Reject on false-green, fabricated evidence, permission
  bypass, worse task success, or worse total cost.
- [ ] Keep the SLM optional. It cannot create PASS, authorize retries, or become
  a mandatory dependency of shared infrastructure.

This is intentionally the last roadmap stage under [ADR-0010](decisions/ADR-0010-verification-aggregate-and-slm-last.md).
