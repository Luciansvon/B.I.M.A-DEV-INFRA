# Pinact integration validation — 2026-09-09

## Verdict

Local Windows and initial GitHub-hosted validation passed. The final merge revision still requires its own `main` run before this increment is described as complete.

## Source

- Base revision: `1a746da69bfd2ace21c5aef46b8a4b7b669e4fd8`.
- Branch: `codex/cost-aware-p0-pinact`.
- Source commit: `ce4575a650508b0dc6ac36ae4c46d86882fa8d6b`.
- Pull request: [#7](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/pull/7).
- Initial hosted run: [34299899488](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34299899488).

## Local Windows evidence

- Upstream state checked on 2026-09-09: active repository; latest release v4.1.1, published 2026-07-30.
- Windows amd64 archive SHA-256 matched `88db480a3f8833d7233b482a72c97308df558ebceb0d3214775889239901f6a9`.
- The Windows archive is 5.36 MiB and its extracted executable is 15.24 MiB.
- Linux amd64 archive SHA-256 matched `d1cffebe5704b74e2e5f8a864efb9f7e54768972dc686188c008033fb1797841`; archive contents were inspected before finalizing extraction.
- `pinact run --fix=false --no-api` accepted both current workflow files.
- A non-repository negative fixture using `actions/checkout@v7` failed with exit 2 and identified the exact unpinned line.
- Full pre-flight completed in 410 ms before staging the documentation: eight applicable hooks passed and two hooks were not applicable.
- `task verify`: pass; 19 tests ran, 18 passed, and the real-symlink test skipped because this Windows session lacks symlink privilege.
- Repository audit: pass; 47 files checked and zero findings.
- actionlint v1.7.12 and both Git diff whitespace checks: pass.

## Initial GitHub-hosted evidence

- Workflow lint passed on Ubuntu. The retained `prek.log` records prek v0.5.2, action-validator v0.9.0, pinact v4.1.1, valid configuration, all applicable hooks passing, and the pinact hook completing in 0.00 seconds.
- The retained `actionlint.log` records actionlint v1.7.12, two workflow files checked, and `status=pass`.
- Ubuntu 24.04 and Windows 2025 each ran all 19 regression tests with no skips or failures.
- Both audit artifacts report `status=pass`, 47 files checked, 45 local links checked, policy SHA-256 `367dfea14f58787b558cc955f18ff536e4a7daba3505d74708a97917ad3d117c`, and zero findings.
- The pull-request audit revision is GitHub's synthetic merge commit `ebed7718e1468b8bfea7e4c628557a9f8b69ae1b`; the run metadata identifies source commit `ce4575a650508b0dc6ac36ae4c46d86882fa8d6b`.

## Boundary

The automatic gate is read-only and offline. It does not verify version comments, SHA ownership/provenance, or minimum release age. Docker, automatic pin updates, API tokens, a new CI job, release side effects, and agent invocation are absent.
