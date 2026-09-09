# Agent packet validation — 2026-09-09

## Scope

Final bounded P0 increment from Issue #3: `bima-agent-packet.v1`, its repository-audit failure adapter, local Task entry point, existing GitHub CI/reusable-workflow integration, and retained evidence paths. No automatic agent invocation, retry, extra runner job, Docker dependency, credential, release, or consumer integration was added.

## Local evidence

`task verify` passed on Windows with the pinned Task 3.53.1, prek 0.5.2, action-validator 0.9.0, pinact 4.1.1, zizmor 1.30.0, actionlint 1.7.12, and Python 3.13.15. Results:

- 35 tests ran: 34 passed and the Windows privilege-dependent symlink case skipped; all 8 agent-packet tests passed.
- Pre-flight hooks and workflow lint passed; zizmor reported no findings and one documented suppression.
- Repository audit checked 63 files and 68 supported local links with zero findings.
- Dirty-tree canonical evidence hash after implementation commit `e9c5ced`: `8900fde7e095e0d8d7c7454dd7b5677b85285f175826c98a31334d8504e7657b`.
- The pass route printed `agent-packet: not-needed; status=pass` and left no owned packet files.
- Synthetic unit fixtures verified deterministic `fail -> machine` and `error -> agent` output, exact hashes, list/string caps, stale-output cleanup, strict canonical input, and sanitized invalid-input failure.

The dirty-tree hash is local implementation evidence only. It is not expected to equal the clean hosted commit hash because revision and dirty state are semantic canonical fields.

## Hosted pull-request evidence

PR [#12](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/pull/12), implementation commit `e9c5ced`, run [`34322360536`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34322360536) passed all three jobs. GitHub evaluated synthetic merge revision `dae938aacdf021c8351ad9618c0a64fff4fe0bb2`.

- Workflow lint/pre-flight passed with the pinned tools and retained logs.
- Ubuntu 24.04 and Windows 2025 each ran 35/35 tests successfully.
- Both audits checked 63 files and 68 supported local links with zero findings.
- Both exact `canonical.json` files had SHA-256 `892b30ea18bc9efea96c391b68fc858a14e8b749c2547a337be14ec9be346b57`.
- Both packet steps logged `agent-packet: not-needed; status=pass`.
- Downloaded artifacts contained zero `packet.json` and zero `packet.sha256` files, confirming the pass-path absence contract rather than merely trusting step success.

Artifact snapshot retained locally under `work/evidence/agent-packet-pr12-run-34322360536/` outside the repository.

## Hosted main evidence

Pending merge run.

## Boundaries

- A pass intentionally produces no agent packet.
- A deterministic audit failure routes to `machine`; only an unclassified audit error routes to `agent`.
- Packet content is untrusted data and cannot grant execution authority.
- Findings, error codes, affected paths, and strings are bounded; raw logs and volatile runtime data are excluded.
- `repeatable` is not measured (`null`) and no retry is attempted (`0`).
- The adapter covers repository audit only. Cross-project consumption and non-audit stages remain unverified.
