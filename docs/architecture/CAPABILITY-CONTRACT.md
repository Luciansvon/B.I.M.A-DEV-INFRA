# Capability, policy and evidence contract

Status: **Accepted design contract under [ADR-0009](../decisions/ADR-0009-capability-verification-architecture.md); runtime implementation pending.**
Date: 2026-09-10. Current executable contracts remain the linked v1 standards.

## 1. Ownership and deployment

Projects declare commands, expected results, required capabilities and resource needs. Shared infrastructure validates the declaration, applies trusted policy, executes a reviewed adapter and produces evidence. Logical capabilities are CLI/module boundaries; they do not require network services or a universal plugin framework.

Precedence is: trusted infrastructure restrictions plus explicit user/workflow authorization; reviewed project policy within that boundary; provider capability limits. A project may narrow permission but cannot expand the infrastructure boundary. Discovery, source files, model output and MCP annotations are input data, never authorization. Configuration modified by the subject PR is not trusted merely because it passes schema validation.

The initial executable project/policy profile should use strict versioned JSON to reuse the existing parser/validation approach. `.bima/project.yml` in earlier RFCs is conceptual, not a supported file. No runnable profile is introduced by this document. A later YAML frontend requires an explicit parser/security and migration decision.

## 2. Operation request and authorization

An operation request identifies project, immutable subject revision/artifact digest, adapter/version, actor supplied by the trusted host, operation class, command reference, resource scope, network destinations, output root, limits and idempotency key where relevant. Project commands are executable code: use bounded argument arrays or a separately reviewed script entry point, never interpolation of untrusted issue/log text into a shell.

| Class | Examples | Default decision |
|---|---|---|
| Inspect | Read scoped source or normalized evidence | Allow within existing authorization and path limits |
| Verify | Run tests/build/scan | Allow only in a runner approved for that subject and command trust level |
| Modify | Patch disposable checkout, open PR | Requires a matching authorized workflow/user scope |
| Provision | Create sandbox/database branch | Requires allowed provider, resource ownership, budget and cleanup plan |
| Promote | Add a reviewed reusable failure record | Requires confirmed evidence and authorized record review |
| Publish/destructive | Release, production deployment, delete persistent data | Human approval bound to exact operation/target |
| Bypass | Self-approval, disable trusted verifier, erase failure evidence | Deny |

Decision values are `ALLOW`, `HUMAN_REQUIRED`, `DENY`. Conditions are explicit obligations: an unsatisfied condition is not an executable allow. Invalid/unknown policy returns a non-executable error. It never falls back to allow.

Minimum decision record:

| Field | Meaning |
|---|---|
| `decision_id`, `schema` | Traceable decision and contract version |
| `request_digest` | Digest of the complete normalized operation request |
| `policy_revision`, `policy_hash` | Exact trusted policy identity |
| `rule_ids`, `decision`, `reason_code` | Applied rules and machine-readable explanation |
| `obligations` | Allowed paths, permissions, destinations, timeout, output and cleanup limits |
| `approval_ref` | Verified approval identity/reference when required; a caller-written string is insufficient |
| `budget` | Allowed calls/runtime/spend and reservation; actual use recorded separately |
| `issued_at`, `expires_at` | Execution metadata; stale decisions must be re-evaluated |

The executor validates the decision and request binding immediately before execution. Changed revision, diff, command, policy, resources, approval expiry or retry attempt triggers a new decision. Each consequential operation goes through the gate; a general allowance at task start cannot authorize all future side effects.

Start with zero autonomous model calls and no external provisioning unless a reviewed policy explicitly allows them. Reserve bounded resources before dispatch; retries consume the same task budget. Concurrent dispatch requires atomic reservations or serialized ownership. A changed attempt ID cannot reset the task budget. Record actual usage when available and identify estimates; unknown cost cannot be reported as zero. Budget exhaustion produces BLOCKED for work still required.

A policy file is not a sandbox. Enforcement must live in the trusted runner's credentials, filesystem/process isolation, network controls and protected workflow. An executor that cannot enforce required constraints must refuse the operation. Untrusted subject code must not write the verifier, approvals, policy, budget ledger or final accepted evidence. The present developer shell is not claimed as such a security boundary.

## 3. Capability and provider boundary

| Capability | Baseline/target | Activation boundary |
|---|---|---|
| Verification | Existing repository audit; later explicit test/build/security adapters | Required checks defined by project contract |
| Execution | Local trusted checks + GitHub Actions CI | Specialized runners only with declared trust/resource requirements |
| Repository intelligence | Native search/read | Graphify code-only experiment after baseline tasks exist |
| Failure memory | Reviewed project incident records; future SQLite + FTS5 index | Confirmed records and retrieval need |
| Intelligence | Deterministic rules, then authorized agent work | Optional SLM must pass #9's benchmark gate |
| Sandbox execution | Disabled | A disposable-run use case and enforceable isolation/cleanup |
| Durable workflow | Disabled | Real pause/resume requirement beyond current CI |
| Database sandbox | Disabled | Real database consumer; disposable project-compatible DB before a hosted branch provider |
| Security response | Disabled | Repeated security case-management need |
| Human control | GitHub Issues/PRs | External UI only if a measured workflow need emerges |

A provider request/result uses the capability's versioned contract, preserves native outputs, and includes provider/version, subject, operation/attempt IDs, request/decision references, lifecycle status, evidence manifest, usage and cleanup result. CLI, API and MCP are interchangeable transports, not interchangeable trust guarantees. A provider supplies observations; the trusted adapter/verifier applies acceptance rules.

The evidence manifest lists each expected file/ref, digest, size, media type, role, owning project, sensitivity and retention location. Validate path containment, links, size and identity before accepting content. Remote refs require authorized retrieval; metadata must not cause arbitrary URL fetching. Successful process exit with missing/wrong-subject output is invalid evidence.

An optional provider may degrade to an approved baseline only if all required capabilities remain satisfied. Record the omission/fallback. Required unavailable provider or unsupported operation yields BLOCKED. Optional capability failure remains visible in that capability's result; it does not disappear into the required-scope PASS. Unknown provider IDs/versions fail profile validation. No vendor-specific logic may override required checks.

Provisioning requires resource IDs, owner/task binding, deadline, cancellation handling and idempotent teardown. Export evidence before teardown. Cleanup failure is recorded as a required operational check (BLOCKED while remediation is pending, or FAIL if a cleanup assertion demonstrably fails). Failed resources are never silently abandoned or retried indefinitely. Signing and external publication use separate approvals and scoped credentials.

## 4. Result axes and aggregation

Keep these distinct in the target model:

| Axis | Values/meaning |
|---|---|
| Execution lifecycle | queued, running, completed, errored, timed_out, cancelled, unavailable |
| Attempt outcome | pass, fail, unknown, not_run; native status and exit code also retained |
| Applicability | required, optional, not_applicable, with reviewed scope/reason |
| Stability | unassessed, consistent_observed, flaky, with attempt/registry refs |
| Aggregate verdict | PASS, FAIL, UNKNOWN, BLOCKED for the declared required scope |
| Authorization | ALLOW, HUMAN_REQUIRED, DENY; independent of verification truth |

Deterministic aggregation order for a fixed required-check set:

1. FAIL if any required check has valid evidence of failure; retain other blockers/unknowns too.
2. Otherwise BLOCKED if a required check could not run/complete because of permission, provider, environment, cancellation or timeout, or cleanup remains unresolved.
3. Otherwise UNKNOWN if required evidence is missing, malformed, from the wrong subject, uninterpretable or insufficient. An unexplained zero-test run is UNKNOWN when tests were expected.
4. Otherwise UNKNOWN if equivalent required attempts disagree and no reviewed resolution exists; record `stability=flaky`. A UI may display FLAKY prominently.
5. Otherwise PASS only when every required check has acceptable evidence, with no unresolved obligations. An empty required-check set is UNKNOWN, unless the declared operation explicitly verifies an empty set as its meaningful assertion.

Within a retry group, preserve every attempt. Mixed valid pass/fail attempts with the same subject, policy, command, declared environment, inputs and equivalent reset state are flaky; they do not independently prove a consistently failing check for step 1. A separate reproducible failure still wins. One failed attempt followed by a passing run after a code/policy/environment change is a new verification sequence, not proof of flakiness. A transient execution error followed by a completed pass is recorded as recovered execution, not automatically a flaky test.

No model can override these rules. An SLM classification cannot create PASS, authorize retry, or prove a test is flaky. A warning is advisory metadata unless project policy makes it a required failure. A skip is not a pass. A waiver must name owner, scope, reason and expiry; it may change applicability only through reviewed policy and must not rewrite historical outcomes. Security/provenance checks cannot be removed through an agent-authored waiver.

For protected merge/release checks, only aggregate PASS maps to a successful required GitHub check. UNKNOWN/BLOCKED/unresolved flaky states map to a non-successful gate, never neutral/skipped-as-success. Human release approval is an additional independent condition even after verification passes.

## 5. Evidence storage and v1 compatibility

Current v1 status remains `pass | fail | error`. [EVIDENCE-CONTRACT](../standards/EVIDENCE-CONTRACT.md) and [AGENT-PACKET](../standards/AGENT-PACKET.md) remain executable truth. Current generators clear owned scratch outputs; these are not immutable historical storage.

Target design: semantic result plus separate execution metadata and a manifest of native attachments. Store finalized evidence in per-operation/per-attempt locations with digest references; correction adds a new linked record. Hash equality establishes only equality of recorded content. Trust also requires subject, policy, producer identity and, where required, verified attestation. An Actions job reporting success does not supply these checks automatically.

Environment constraints affecting a claim (OS, architecture, toolchain, fixture/DB snapshot, relevant dependency data) belong to its semantic scope. Host names, timestamps and durations remain execution metadata. Cross-platform equivalence is adapter-defined; do not claim Windows behavior from a Linux result or compare different environments blindly.

Migration requirements before v2 is enabled:

1. Preserve v1 inputs/outputs and deployed pins. Introduce separate v2 paths/reader selection; do not add fields to existing strict v1 JSON.
2. Define explicit mappings: v1 pass -> PASS, fail -> FAIL, and error -> UNKNOWN unless retained details establish a concrete blocker. Never guess a retry or stability history from v1.
3. Preserve `packet.v1` field meanings; its `artifact_hash` is the canonical input digest, not an application binary digest. Use explicit subject/evidence/artifact digest names in the new contract.
4. Keep raw/semantic digests version-scoped. Do not compare v1 and v2 bytes or expected hashes directly.
5. Test positive/negative mappings, missing evidence, policy denial, cancellation, wrong subject, flaky attempts, stale approvals and expired refs. Verify both the external fixture and AI-COLOR-COMPARE before changing their pins.
6. Retain a rollback path to the prior reviewed pins and evidence readers. Do not relabel historical artifacts or mark migration complete without hosted evidence.

Routine Actions evidence currently retains for 14 days. Promoted failure cases must retain approved, sanitized supporting data in a project-owned durable location before expiration. Missing/expired backing evidence marks memory REVALIDATION_REQUIRED and prevents automatic reusable-fix use. A digest without available content is not permanent proof. No immutable-storage service is claimed to exist yet.

## 6. Failure memory and benchmark gates

Record fields must cover case ID, project, subject/environment, signature and version, reproduced failure refs, confirmed cause, fix revision/class, verification scope/result, reviewer, provenance, sensitivity, status, supersession and revalidation trigger. A signature match only returns a candidate remedy; it never executes a patch or declares the new case solved.

Promotion requires reviewed causal support: failure reproduced before the fix, relevant regression passes after it, unchanged acceptance rules or a separately justified rule change, and no unresolved flaky/blocked evidence. Scope-specific success is not proof of a universal cause. Local-only evidence remains labeled; authoritative project verification requirements still apply.

Lifecycle: ACTIVE, SUPERSEDED, EXPIRED, INVALIDATED, REVALIDATION_REQUIRED. Query only records valid for the project, environment and rule version by default. Project records stay with the project; global promotion requires shared-infrastructure cause or the same confirmed cause in at least two projects. Cross-project retrieval respects data-access permission even when a case seems relevant.

Use versioned reviewed JSON case records/refs as the portable source and a rebuildable SQLite + FTS5 index outside synchronized/network folders. Start with a single local writer; do not share a live SQLite file across runners. Export consistent snapshots, verify imports and test restore/rebuild. This is an implementation choice for memory, not a global database requirement for every project.

Distinct gates:

- Schema/record collection can begin with the first verified case. No 100-case prerequisite for designing a format or recording evidence.
- Retrieval pilot: at least 100 real verified failure/fix cases before drawing useful pilot conclusions, as proposed by #15. Keep fixed held-out queries; report small-sample limits and relevance labels. A larger corpus is required for stronger claims or backend selection.
- SLM runtime/training: deterministic preprocessing, a real relevant consumer and at least 1,000 verified benchmark cases in the total corpus, with explicit training/development/test counts, case-family deduplication and time/project separation. This preserves #9's minimum; it does not invent 1,000 held-out cases. #9's category example sums to 1,150 and is treated as an illustrative larger allocation, not a validated dataset.
- Healthy/noisy/unknown benchmark examples require validated labels but do not become reusable fix memories without a confirmed fix. Hidden test labels/future fixes must be inaccessible to tuning agents and retrieval indexes. Optimize on development data; evaluate once on a frozen test split, then version a new benchmark for later tuning.

Compare exact rules and FTS/BM25 before models/embeddings. Pre-register thresholds, representative tasks, seeds, hardware, cold/warm costs and confidence reporting. Report retrieval recall, false matches, stale hits, diagnosis/verification success, total time and calls including retries/index construction. A model's confidence is not calibrated evidence by default. Zero observed critical errors is an acceptance requirement for the pilot, not a guarantee of zero future risk. Any false-green, fabricated evidence or permission bypass rejects activation.

Graphify experiments use matched tasks on DEV-INFRA and AI-COLOR-COMPARE, with pinned upstream revision and code-only mode first. Include docs/config/dynamic-wiring failures that an AST index might miss. Use the same source snapshot, agent/model, task budget and acceptance tests; account for build/update overhead and avoid leaking solutions between runs. Do not adopt if task success declines or savings disappear after total cost. No numerical improvement threshold is claimed until the baseline and pilot budget are recorded.

## 7. Release and specialized consumers

ReleaseProof verifies two independent claims about one identified artifact: source/build provenance and installed/runtime behavior. Require expected app identity/version, intended Lite/Full differences and project-owned installer assertions. Build/package/sign transformations must record input/output digests; test the final distributed bytes and publish those same bytes. Signing after testing without re-verifying the changed artifact violates the same-artifact rule.

Checksums, SBOMs, signatures and valid attestations each prove limited properties. Release-note assertions use stable claim IDs linked to tests/evidence, and unsupported claims remain unverified. Model prose never satisfies a release requirement. Untrusted installer/binary inspection needs runner isolation and exported evidence before teardown; no GUI or Windows capability is presumed from a provider's CLI support.

For a future PostgreSQL consumer, start with an isolated disposable database and project-owned synthetic/sanitized fixtures. Database branching, migration execution, scanner credentials and cleanup are separate permissions. pgbot inspection is a candidate; its AI explanation features are outside deterministic verification. Other databases use their own adapters without introducing PostgreSQL into the core.

## References

See the [source ledger](../research/SOURCES-ARCHITECTURE-2026-09-10.md): S01–S09 execution, S10–S20 evidence/authority, S21–S31 memory/evaluation, S32–S40 optional execution, S41–S52 specialized adapters. These requirements are B.I.M.A design decisions informed by those sources and the [plan audit](../audits/ARCHITECTURE-PLAN-AUDIT-2026-09-10.md).
