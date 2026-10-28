# Worklog

## 2026-09-08 — Audit and first executable foundation

Audited remote `main` at `f4d0d1538c6b7ecdc5c1c6cb1b32fa74c49fce14` and repository settings. Created local branch `codex/infra-audit-foundation` in a separate clone. Added the experimental offline repository audit, caller policy, failure reports, regression tests, reusable workflow, two-OS CI definition, Actions update configuration, and operational documentation. Kept existing research ledgers intact.

Validation: 18 test cases passed and 1 Windows symlink case skipped; actionlint 1.7.12 accepted both workflows; repository audit completed with no findings after documentation was complete. Exact logs, counters, and limitations are recorded in the [validation record](audits/VALIDATION-2026-09-08.md). A mistaken depth-limit assumption in a test was corrected; its earlier failing log was preserved.

Published commit `9722c420202dafc0733fb536e9c46b1d2b9db625` in PR #1. Its initial hosted Ubuntu/Windows jobs passed all tests and audits, including symlink handling. Artifact comparison exposed platform-dependent LF/CRLF hashes; a follow-up enforces LF, adds verified workflow lint to CI, and removes duplicate branch-push runs when pull-request CI exists. Final hosted evidence and merge state are recorded by GitHub history and the validation record. No external consumer change, license assignment, branch-protection update, or project application change was made. See [audit findings](audits/AUDIT-2026-09-08.md) and [next steps](NEXT.md).

## 2026-09-09 — Cost-aware P0 command contract

Read and adopted Issue #3 before continuing infrastructure work. Converted Dagger PR #2 to Draft/Deferred because its portability work is sequenced after the deterministic P0 foundation. Started a clean branch from `main` for the first bounded P0 increment: a pinned Task command contract wrapping the existing audit, regression tests, workflow lint, and diff checks. PR #4 run `34293104738` passed workflow lint plus Ubuntu/Windows audit jobs; downloaded artifacts confirmed 19/19 hosted tests on both operating systems, matching audit hashes/counters, and zero findings. Exact evidence and boundaries are recorded in the [Task validation record](audits/VALIDATION-2026-09-09-TASKFILE.md).

## 2026-09-09 — Cost-aware P0 pre-flight hooks

Started the next bounded Issue #3 increment from merged `main`. Added prek v0.5.2 using a single `prek.toml`, bundled non-mutating hooks, and `task preflight`. Reused the existing workflow-lint job instead of creating another runner job, with a checksum-verified release binary and a separate retained log. Local Windows configuration, hook execution, full Task verification, and both release archive checksums passed. PR #5 run `34296977597` then passed the pre-flight/workflow-lint job plus both hosted audit jobs; downloaded artifacts confirmed all applicable hooks, 19/19 tests on both operating systems, matching audit hashes/counters, and zero findings. Exact results and limitations are recorded in the [prek validation record](audits/VALIDATION-2026-09-09-PREK.md).

## 2026-09-09 — Cost-aware P0 workflow schema validation

Started the next bounded Issue #3 increment from merged `main`. Added action-validator v0.9.0 to the existing prek and workflow-lint path without another job. The Linux release binary is checksum-verified in CI; because upstream publishes no Windows binary, local Windows evidence uses the pinned crates.io package. Both current workflow schemas passed locally, while an isolated unmatched-path fixture failed with the expected code. PR #6 run `34298864689` passed workflow/pre-flight plus both audit jobs; downloaded artifacts confirmed action-validator execution, 19/19 tests on both operating systems, matching audit hashes/counters, and zero findings. Exact results and limitations are recorded in the [action-validator validation record](audits/VALIDATION-2026-09-09-ACTION-VALIDATOR.md).

## 2026-09-09 — Cost-aware P0 immutable Action references

Started the next bounded Issue #3 increment from merged `main`. Added pinact v4.1.1 as a read-only, offline prek hook and reused the existing workflow-lint job. Both Linux and Windows release checksums passed; current workflows passed the full-SHA check, while an isolated mutable-tag fixture failed on the exact line. PR #7 run `34299899488` passed workflow/pre-flight plus both audit jobs; downloaded artifacts confirmed pinact execution, 19/19 tests on both operating systems, matching audit hashes/counters, and zero findings. Exact results and limitations are recorded in the [pinact validation record](audits/VALIDATION-2026-09-09-PINACT.md).

## 2026-09-09 — Cost-aware P0 GitHub automation security

Started the next bounded Issue #3 increment from merged `main`. Added zizmor v1.30.0 as a regular-persona, read-only offline prek hook and reused the existing workflow-lint job. The initial scan found an insufficient Dependabot cooldown; setting the documented seven-day delay cleared the medium finding without delaying security updates. Current automation then passed, while an isolated template-injection fixture failed with a high-severity finding and exit 14. PR #10 run `34317309966` passed workflow/pre-flight plus both audit jobs; downloaded artifacts confirmed zizmor scanned all three selected files, 19/19 tests passed on both operating systems, audit hashes/counters matched, and no findings remained. Exact results and limitations are recorded in the [zizmor validation record](audits/VALIDATION-2026-09-09-ZIZMOR.md).

## 2026-09-09 — Cost-aware P0 canonical evidence

Started the next bounded Issue #3 increment from merged `main`. Added a standard-library repository-audit adapter for the versioned `bima-evidence.v1` envelope. Semantic fields serialize deterministically and receive a SHA-256, while timestamp, runtime, and raw-result digest remain in separate execution metadata. Both the local Task contract and reusable workflow preserve raw and normalized evidence without adding a runner job or external dependency. PR #11 run `34319510404` passed workflow/pre-flight plus both audit jobs; downloaded artifacts proved the Ubuntu and Windows canonical files were byte-identical while their execution metadata remained platform-specific. Exact results and limitations are recorded in the [canonical evidence validation record](audits/VALIDATION-2026-09-09-CANONICAL-EVIDENCE.md).

## 2026-09-09 — Cost-aware P0 bounded agent packet

Started the final bounded Issue #3 P0 increment from merged `main`. Added a standard-library `bima-agent-packet.v1` generator that creates no output for a pass, routes known deterministic audit findings to the machine lane, and marks only unclassified audit errors as eligible for agent escalation. Packet lists and strings are capped, raw logs and prompts are excluded, stale owned outputs are cleared, and neither the local nor GitHub adapter performs retries or invokes an agent. PR #12 run `34322360536` passed workflow/pre-flight plus both audit jobs; downloaded artifacts confirmed 35/35 hosted tests per operating system, matching audit counters and canonical hashes, zero findings, and the intentional absence of pass-path packets. Final evidence is tracked in the [agent packet validation record](audits/VALIDATION-2026-09-09-AGENT-PACKET.md).

## 2026-09-10 — Bounded Policy Gate v1

Implemented strict project, trusted-policy, operation-request and decision contracts plus one fail-closed executor for the existing `repository-audit.v1` operation. The gate binds project/repository identity, full subject revision, exact trusted policy bytes, request digest, actor, validity window, output scope, timeout, attempt budget, and empty network/credential scope. PR #19 merged at `60ec750974f922805ef418a5adef3f992603f8e3`. Post-merge run `34442172182` passed workflow lint and both hosted audit jobs; downloaded Ubuntu and Windows artifacts each contain 49 passing tests, 83 audited files, 140 local links, zero findings, identical canonical SHA-256 `c671edefe36c6d865b9b6099032f6f9ad82ac7c61faba21e87f9e577c5677afe`, and no pass-path agent packet. Real-consumer compatibility and license selection remain pending. See the [Policy Gate validation record](audits/VALIDATION-2026-09-10-POLICY-GATE.md).

## 2026-09-10 — Policy Gate hosted evidence (#20)

Recorded the post-merge Policy Gate evidence in `e70e5b9`; the run and artifact details remain in the preceding entry and the [Policy Gate validation record](audits/VALIDATION-2026-09-10-POLICY-GATE.md). No contract, workflow pin or consumer changed.

## 2026-09-10 — Deterministic result normalization v2 pilot (#21)

Added the additive `bima-normalization-request.v1` and `bima-verification-result.v2` contracts plus a bounded Rust libtest and TypeScript diagnostic normalizer. Missing summaries, count mismatches and exit/result disagreement stay `UNKNOWN`, and raw logs are excluded. Local validation recorded 12 focused and 61 total tests, 92 files, 143 links and zero findings in the [result normalizer validation record](audits/VALIDATION-2026-09-10-RESULT-NORMALIZER.md).

## 2026-09-10 — Result normalizer hosted evidence (#22)

Post-merge Infrastructure CI run `34444750180` passed at `828ae90` with 61 tests on Ubuntu 24.04 and Windows 2025, 92 audited files, 143 links and zero findings; canonical evidence matched across both systems. See the [result normalizer validation record](audits/VALIDATION-2026-09-10-RESULT-NORMALIZER.md).

## 2026-09-10 — Bounded known-failure registry (#23)

Added the exact-match `bima-known-failure-registry.v1` and classification contracts with mandatory owner/reviewer, a 90-day maximum expiry and `automatic_retry_allowed=false`. Changed diagnostics, expired entries and duplicate definitions fail closed; no retry or repair path exists. Local validation recorded 11 focused and 72 total tests, 100 files, 146 links and zero findings in the [known-failure registry validation record](audits/VALIDATION-2026-09-10-KNOWN-FAILURE-REGISTRY.md).

## 2026-09-10 — Known-failure registry hosted evidence (#24)

Post-merge Infrastructure CI run `34446812166` passed at `d342504` with 72 tests on both hosted operating systems, 100 audited files, 146 links and zero findings; canonical audit evidence matched across systems. See the [known-failure registry validation record](audits/VALIDATION-2026-09-10-KNOWN-FAILURE-REGISTRY.md).

## 2026-09-10 — Shared Rust result normalization action (#25)

Added a composite action and `bima-normalization-config.v1` so the CI matrix can invoke normalization from runtime-bound inputs. DEV-INFRA run `34470140936` passed at `d748b66` on both operating systems with `PASS`, `ALL_EXPECTED_TESTS_PASSED` and `29/29`; consumer migration was closed without a change. See the [result normalization action validation record](audits/VALIDATION-2026-09-10-RESULT-NORMALIZATION-ACTION.md).

## 2026-09-12 — Trusted launcher and gated failure-memory core (#26)

Added the SHA-bound trusted repository-audit launcher, reviewed failure-record contract, SQLite/FTS5 index and benchmark gates, deterministic experiment gate and Apache-2.0 license. After three first-attempt portability defects were fixed, replacement hosted run `34707376740` passed lint and both OS matrices, and launcher run `34707376819` returned `ALLOW` with a passing 144-file subject audit. Failure memory stayed `BLOCKED` at `0/100` real cases and `0/10` held-out queries, no experiment activated, and no consumer pin changed. See the [P0-P5 validation record](audits/VALIDATION-2026-09-12-P0-P5.md).

## 2026-09-13 — Failure Memory history audit (#27)

Audited the five failed GitHub Actions runs available at the time and found five technically eligible shared-infrastructure cases; each lacked independent review, so none was activated. Production memory remained at `0/100` records and `0/10` held-out queries without creating a database. See the [history audit](audits/FAILURE-MEMORY-HISTORY-AUDIT-2026-09-13.md).

## 2026-09-13 — Activate five reviewed Failure Memory records (#28)

Activated five canonical public `ACTIVE` records after Bima's independent review in PR #27; `codex-curation` owns transcription and `Luciansvon` is the distinct reviewer. The first hosted attempt (`34730811769`) failed on a stale zero-count assertion, and replacement run `34730928028` passed at the corrected revision with 111 tests per OS and the five-record set. Production memory and the benchmark stayed `BLOCKED` at `5/100` and `0/10`; launcher run `34730928155` returned `ALLOW`. See the [failure-record activation validation](audits/VALIDATION-2026-09-13-FAILURE-RECORDS.md).

## 2026-09-13 — Spec Kit adapter architecture audit (#29)

Audited Spec Kit `v1.0.6` against 74 sources and approved it only as a gated, optional authoring adapter candidate, not as governance, verification or release authority. No package, preset, adapter, workflow or consumer was installed. See the [Spec Kit adapter audit](audits/SPEC-KIT-ADAPTER-AUDIT-2026-09-13.md).

## 2026-09-13 — Sixth reviewed Failure Memory record (#30)

Activated the stale corpus-count assertion from run `34730811769` as the sixth reviewed record, raising the corpus to `6/100` with `0/10` held-out queries and no database. Hosted run `34752079512` passed at the corrected revision with 111 tests per OS, 149 files, 171 links and zero findings; launcher run `34752079705` returned `ALLOW`. See the [sixth activation validation](audits/VALIDATION-2026-09-13-FAILURE-RECORD-006.md).

## 2026-09-13 — Fail-closed verification aggregate (#31)

Added `bima-verification-plan.v1` and `bima-verification-aggregate.v1` with fixed `FAIL > BLOCKED > UNKNOWN > PASS` precedence, unresolved-required tracking and zero-input `UNKNOWN` behavior. Hosted run `34753773782` passed with 127 tests per OS, 158 files, 181 links and zero findings; launcher run `34753773924` returned `ALLOW`. See the [verification aggregate validation](audits/VALIDATION-2026-09-13-VERIFICATION-AGGREGATE.md).

## 2026-09-13 — Fail-closed artifact identity contract (#32)

Added additive request, manifest and verification contracts binding declared artifact bytes to subject/policy, role, ownership, retention metadata, size and SHA-256; missing, changed or unsafe files fail closed. Hosted run `34767179664` passed with 142 tests per OS, 167 files, 188 links and zero findings, and launcher run `34767179786` returned `ALLOW`. The increment is contract proof only: no build/release consumer uses it and consumer migration remains deferred. See the [artifact identity validation](audits/VALIDATION-2026-09-13-ARTIFACT-IDENTITY.md).

## 2026-10-28 - Audit ledger adjudication and low-risk hardening (#33)

Verified the external Final Audit Ledger claim-by-claim. The `4ebd5df` launcher pin and the `upload-artifact`/`setup-python`/`prek`/`zizmor` updates are correct. The ledger's "Pytest 147 PASS, 2 SKIPPED" claim is contradicted by the canonical `unittest` runs (149 tests, 0 skipped, Ubuntu and Windows); its 171-file audit count is local-only because `user.md` is untracked. Added `-I` to both Python calls in the normalization action, ignored `.env*` and `*.pem`, and recorded the subject audit-policy trust gap as [ADR-0012](decisions/ADR-0012-subject-audit-policy-trust.md). No workflow pin, contract, required context, or consumer changed.
