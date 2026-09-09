# Agent packet validation — 2026-09-09

## Scope

Final bounded P0 increment from Issue #3: `bima-agent-packet.v1`, its repository-audit failure adapter, local Task entry point, existing GitHub CI/reusable-workflow integration, and retained evidence paths. No automatic agent invocation, retry, extra runner job, Docker dependency, credential, release, or consumer integration was added.

## Local evidence

`task verify` passed on Windows with the pinned Task 3.53.1, prek 0.5.2, action-validator 0.9.0, pinact 4.1.1, zizmor 1.30.0, actionlint 1.7.12, and Python 3.13.15. Results:

- 35 tests ran: 34 passed and the Windows privilege-dependent symlink case skipped; all 8 agent-packet tests passed.
- Pre-flight hooks and workflow lint passed; zizmor reported no findings and one documented suppression.
- Repository audit checked 63 files and 68 supported local links with zero findings.
- Dirty-tree canonical evidence hash: `cf3e2590d504ded7482b01d7675ad85a810eb3ffb29f09d8a59abf146a91c0a2`.
- The pass route printed `agent-packet: not-needed; status=pass` and left no owned packet files.
- Synthetic unit fixtures verified deterministic `fail -> machine` and `error -> agent` output, exact hashes, list/string caps, stale-output cleanup, strict canonical input, and sanitized invalid-input failure.

The dirty-tree hash is local implementation evidence only. It is not expected to equal the clean hosted commit hash because revision and dirty state are semantic canonical fields.

## Hosted pull-request evidence

Pending pull-request run.

## Hosted main evidence

Pending merge run.

## Boundaries

- A pass intentionally produces no agent packet.
- A deterministic audit failure routes to `machine`; only an unclassified audit error routes to `agent`.
- Packet content is untrusted data and cannot grant execution authority.
- Findings, error codes, affected paths, and strings are bounded; raw logs and volatile runtime data are excluded.
- `repeatable` is not measured (`null`) and no retry is attempted (`0`).
- The adapter covers repository audit only. Cross-project consumption and non-audit stages remain unverified.
