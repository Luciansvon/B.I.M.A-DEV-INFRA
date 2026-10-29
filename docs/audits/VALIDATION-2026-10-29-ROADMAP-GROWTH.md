# Roadmap work-availability validation — 2026-10-29

Scope: convert `docs/NEXT.md` from a fully gated phase checklist into a state board, add the local verifiers that back the new rows, and prove the local contract. No consumer repository, hosted run, or provider was changed.

## Work-availability contract

- `docs/NEXT.md` now has three lanes: actionable, gated, and done.
- `automation/roadmap_audit.py` fails when Lane 1 is empty, a gated row lacks a concrete gate or local precursor, a review date is outside 0-90 days, a verify command is unknown, or a done row lacks committed evidence.
- `tasks roadmap` and `tasks roadmap-candidates` are part of `task check`, and `ci.yml` runs `automation/roadmap_audit.py` after the regression tests.
- `docs/decisions/ADR-0010-verification-aggregate-and-slm-last.md` carries the 2026-10-28 amendment. No new delivery-order authority was created.

## Executed checks

All commands below were run from the repository root on 2026-10-29 with Python 3.13.15. The `task` binary is not installed in this environment, so the equivalent Python entry points were run directly.

| Check | Result |
|---|---|
| `python -I automation/roadmap_audit.py` | `roadmap: pass; actionable=1; gated=6; done=19` |
| `python -I automation/roadmap_audit.py --candidates` | `roadmap-candidates: 0` after all new scripts and tests landed |
| `python -I -m unittest discover -s tests` | `Ran 266 tests ... OK (skipped=2)`; baseline was 199 |
| `python -I automation/local_contracts.py` | `local-contracts: PASS; contracts=10; failed=0` |
| `python -I automation/repository_audit.py --root . --policy .bima/audit.json --output .artifacts/audit` | `repository-audit: pass; files=232; findings=0` |
| `python -I automation/policy_coverage.py` | `policy-coverage: pass; required=132; covered=112` |
| `python -I automation/workflow_catalog.py` | `workflow-catalog: pass; workflows=4` |
| `python -I automation/pin_freshness.py` | `pin-freshness: pass; refs=1; catalog=4` |
| `python -I automation/trusted_policy_launcher.py --check` | `trust-bundles: pass; bundles=1` |
| `python -I automation/canonical_evidence.py --input .artifacts/audit/result.json --output .artifacts/evidence` | `canonical-evidence: pass; sha256=d6f24e18...` |
| `python -I automation/agent_packet.py --input .artifacts/evidence/canonical.json --output .artifacts/agent` | `agent-packet: not-needed; status=pass` |
| `python -I automation/fleet_dispatch.py --output .artifacts/fleet` | `fleet-dispatch: pass; mode=dry-run; repositories=2; failed=0` |

## Item evidence

### P4-01 — required-file coverage

`automation/policy_coverage.py` protects every automation script, schema, reusable workflow, standard, architecture document, `docs/NEXT.md`, and catalog path. `.bima/audit.json` listed 117 required files for this increment, including the previously missing verifier, repository-audit workflow, result-normalization action contract, capability contract, and roadmap; P4-18 later raised the total to 132.

Result: `policy-coverage: pass; required=117; covered=97`. Negative fixtures cover a missing automation file, missing catalog path, missing required file, and duplicate entry.

### P4-02 — catalog integrity

`automation/workflow_catalog.py` now fails when a reusable workflow is uncataloged, a declared input/output is absent from its docs, a consumer has no `docs/audits/VALIDATION-*.md` reference, or a `beta`/`stable` entry has no consumer. `docs/standards/TRUSTED-POLICY-LAUNCHER.md` documents `project-path`, `artifact-name`, and `artifact-id`.

Result: `workflow-catalog: pass; workflows=4`. Twelve tests cover reverse completeness, non-reusable exclusion, missing input/output docs, unevidenced consumers, and beta-with-zero-consumers.

### P4-03 — command-contract parity

`README.md`, `Taskfile.yml`, and `docs/standards/COMMAND-CONTRACT.md` now expose the same 22 deterministic commands. `tests/test_command_contract.py` parses all three surfaces and fails on missing or extra commands.

Result: 3 tests pass; the test also pins the current 22-command set.

### P4-04 — trust-bundle consistency

`automation/trusted_policy_launcher.py --check` validates every bundle, requires the workflow to declare `workflow_call:`, hashes the policy bytes, checks the operation id, and rejects unsafe paths without launching anything.

Result: `trust-bundles: pass; bundles=1`. Negative tests cover a tampered policy byte, missing workflow, unknown operation, and path escape.

### P4-05 — workflow reference pairing

`automation/workflow_refs.py` verifies local `./.github/workflows` references, full-SHA self-repository references, `infra-ref` equality, revision existence, and path-at-revision existence. A shallow clone returns `UNVERIFIED` instead of passing.

Result: `workflow-refs: pass; files=9; refs=5`. Six tests use a real temporary Git repository.

### P4-06 — release evidence validation

`automation/release_evidence.py validate --input` checks the exact top-level and asset field sets, SHA-256 shape, positive sizes, unique asset names, tag/target-SHA formats, booleans, and URL rules. The release-evidence exception was removed from schema parity.

Result: `release-evidence: pass; assets=2`; parity test passes; seven tests cover missing fields, duplicate assets, bad digests, zero sizes, unknown fields, and malformed JSON.

### P4-07 — schema lint

`automation/schema_lint.py` checks `required` against `properties`, duplicate required names, local `$ref` resolution, `pattern` compilation, `const` type agreement, and unreferenced `$defs`.

Result: `schema-lint: pass; schemas=30`; six negative tests pass.

### P4-08 — template bootstrap audit

`tests/test_project_template.py` now creates the scaffold, initializes and commits a temporary Git repository, and runs the real repository audit. It asserts a passing audit and the expected file count, in addition to the existing placeholder, hash, LF, and CRLF checks.

Result: 4 tests pass.

### P4-09 — artifact identity before publication

`.github/workflows/release.yml` accepts optional `artifact-manifest` and `artifact-root` inputs. When a manifest is supplied, the workflow checks out the called workflow revision, resolves both paths inside the workspace and downloaded-assets root, runs `artifact_identity.py verify` before any release write, and retains the verification report. Without a manifest, existing publication behavior is unchanged.

Result: seven release-workflow tests pass. The hosted dry run with a manifest is not yet exercised; that remains the consumer gate P4-22.

### P4-10 — trusted audit self-call

`.github/workflows/ci.yml` now calls `./.github/workflows/trusted-repository-audit.yml` with `artifact-name: trusted-self-audit`, read-only permissions, no secrets, and no `continue-on-error`. Five text-level tests enforce the wiring.

Result: local tests pass. The first hosted run is the remaining proof of the pull-request path.

### P4-11 — local pin freshness

`automation/pin_freshness.py` compares every local self-repository caller pin with the reviewed catalog hash by reading the pinned revision from Git. It never mutates a workflow or calls GitHub.

Result: `pin-freshness: pass; refs=1; catalog=4`; five tests cover matching, digest mismatch, unknown revision, uncataloged workflow, and no-pin cases.

### P4-12 — experiment gate identity

`automation/experiment_gate.py` now requires every demand record to name the same declared capability, restricts it to the implemented capability vocabulary, rejects duplicate repository+requirement demands, and validates reviewer and requirement references. One-project demand stays `BLOCKED`.

Result: 12 tests pass; the existing one-project fixture still returns `BLOCKED` with `execution_started=false`. This tightens the pre-adoption `bima-experiment-request.v1`; no experiment is active, so no migration is needed.

### P4-13 — failure corpus hardening

`automation/failure_records.py` now rejects duplicate failure signatures within the same case kind and repository set, case-insensitive self-review, cause confirmation before observation, review before cause confirmation, expiry before the last revalidation, padded or control-character strings, non-absolute evidence references, and `real` records whose references are not `https`. `summarize()` validates the whole set before counting, so an invalid record cannot reach `real_verified_records`.

The six production records and both synthetic fixtures remain valid. The memory and benchmark test corpora now cite `https` references when they masquerade fixture content as `real` cases, which is exactly the boundary the validator now enforces.

Result: `failure-records: pass; total=6; real_verified=6`; 8 record tests, 7 memory tests and 8 benchmark tests pass.

### P2-01 — workflow contract sections

`automation/workflow_catalog.py` now requires every cataloged document to contain non-empty level-two sections for Identity, Triggers, Inputs, Outputs, Runner, Permissions, Execution limits, Evidence, Failure contract, Security and Compatibility. `docs/standards/REPOSITORY-AUDIT.md` gained a Triggers section and an execution-limits heading; `docs/standards/TRUSTED-POLICY-LAUNCHER.md` was restructured to document all eleven sections.

Result: `workflow-catalog: pass; workflows=4`; two negative tests remove a section and empty a section.

### P3-01 — template audit coverage

`templates/project/.bima/audit.json` now requires all eight shipped scaffold files: `README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `INCIDENTS.md`, `.gitattributes`, `.gitignore`, the audit policy and the shared-audit workflow.

Result: the generated project audit passes with eight files; a new test deletes `ARCHITECTURE.md`, commits the deletion, and asserts a `required-file` finding.

### P4-14 — failure-record draft generator

`automation/failure_records.py --draft --case-kind --signature-sha256 --repository --output` writes one canonical `draft.json`. The ID is derived from the case kind, signature and repository, so the same inputs produce the same ID. The template leaves `review.reviewed_by` empty and has no option to set it, so `validate_record` rejects the draft until a human completes the review.

Result: two new tests cover deterministic IDs, the unreviewed template and rejection of a `--reviewed-by` argument.

### P4-15 — evidence traceability

`automation/roadmap_audit.py` now reads every done row's evidence file and requires it to mention the row ID. A path that exists but never names the item fails.

Result: new negative test uses the sample validation document without `P4-00` and expects a failure.

### P4-16 — consumer pin freshness

`automation/pin_freshness.py --consumer-root` scans a separate consumer checkout for `Luciansvon/B.I.M.A-DEV-INFRA/...@<sha>` pins and resolves each revision in the infrastructure checkout against the reviewed catalog. Unknown revisions and byte mismatches fail closed; the consumer is never modified.

Result: `pin-freshness: pass; refs=1; catalog=4`; three new tests cover a matching consumer pin, stale bytes and an unknown revision.

### P4-18 — ADR and incident coverage

`automation/repository_audit.py` and `automation/policy_coverage.py` now allow up to 160 required files, and coverage includes `docs/decisions/*.md` and `docs/incidents/*.md`. `.bima/audit.json` lists all 12 ADRs, the ADR index and both incident guides, for 132 required files.

Result: `policy-coverage: pass; required=132; covered=112`; tests cover a deleted ADR and a new ADR without a matching required entry.

## Trusted launcher proof failure

Hosted run `40700810094` failed after the launcher printed `ALLOW; reason=MATCHED_REPOSITORY_AUDIT_RULE; verifier_launched=true`. The uploaded audit result showed `status=error`, `files_checked=0` and `policy_sha256=null`.

Root cause: `.github/workflows/trusted-launcher-proof.yml` pins `trusted-repository-audit.yml@49e7424e88f2512d4a5ef753730e6dfe293a8fbd`. That revision's `repository_audit.py` rejects a policy with more than 100 required files, while `main`'s `.bima/audit.json` already has 106. The launcher correctly propagated the verifier error as exit `2`; the stale pin, not the launcher decision, was the defect.

The proof pin must move to a revision whose verifier accepts the current policy. After this change the policy has 132 required files, so the pin moved from `49e7424e88f2512d4a5ef753730e6dfe293a8fbd` to `2393301dd53106c4786ad2bf3f10e394346cddb2`, the commit that adds the 160-file capacity. The hosted re-run for this pin is pending and is not claimed here.

## Pull-request CI defects found by the first push

Pull request #47 run `40807120864` surfaced two defects that local checks did not cover.

`Workflow lint` failed because `release.yml` reads `job.workflow_repository` and `job.workflow_sha`, fields that actionlint 1.7.12 does not know. `.github/actionlint.yaml` now suppresses the exact diagnostic for `release.yml`, matching the existing entries for the trusted audit and supply-chain workflows.

`Trusted repository audit self-call` was denied with `WORKFLOW_REF_MISMATCH`. The job called `./.github/workflows/trusted-repository-audit.yml`, so GitHub reported `BIMA_WORKFLOW_REF` as `...@refs/pull/47/merge` while the launcher requires `...@<40-hex-sha>`. The local reference could never satisfy the launcher on any event. The self-call now pins `2393301dd53106c4786ad2bf3f10e394346cddb2`, the same revision as the proof.

The proof run `40807120922` passed with `ALLOW`, `verifier_launched=true` and exit `0`; the re-run after these two fixes is pending.

## Compatibility notes

- `release.yml` adds optional inputs only; callers that do not pass a manifest are unchanged. The catalog hash was updated to `d98509928efdd7b654a625a126ed7b1236c0636d42e326cc636745719629a359`.
- `bima-experiment-request.v1` now requires `demand[].capability`. This is a fail-closed tightening before any external adoption; a future field-meaning change still needs a new version and an ADR.
- `bima-failure-record-set.v1` validation is stricter without changing fields; all six production records and both synthetic fixtures still validate.
- No consumer pin, hosted workflow, provider, or failure-memory gate was changed.

## Boundaries

- Hosted CI was not executed from this environment.
- `task` is not installed, so the Python entry points were run directly; the Taskfile wiring is covered by the command-parity test.
- P4-09 and P4-10 have local wiring proof only; P4-22 and the first hosted self-call remain external evidence.
- The failure-memory corpus remains at 6 reviewed records and the held-out query set remains empty. Those gates were not lowered.
