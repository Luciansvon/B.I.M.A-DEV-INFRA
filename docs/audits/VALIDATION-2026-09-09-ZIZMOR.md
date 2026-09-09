# Zizmor integration validation — 2026-09-09

## Verdict

Local Windows and initial GitHub-hosted validation passed. The final merge revision still requires its own `main` run before this increment is described as complete.

## Source

- Base revision: `c8c5ed3403d56b5905369fbb0e0c7d9d1fc4b0c5`.
- Branch: `codex/cost-aware-p0-zizmor`.
- Initial source commit: `0a5414652b2151114b398d59f637ac592c715154`.
- Pull request: [#10](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/pull/10).
- Initial hosted run: [34317309966](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34317309966).

## Local Windows evidence

- Upstream state checked on 2026-09-09: active MIT-licensed repository; latest release v1.30.0, published 2026-08-30.
- Windows x86-64 archive SHA-256 matched `a2fcf298b84d3d8498a3d718bb63f0abe26823bf68a11f0f439620f8f2f878f0`; archive size was 8,244,779 bytes and the extracted executable was 24,437,248 bytes.
- Linux x86-64 archive SHA-256 matched `ec8c95cd800845abb9bbc5f377ec7c57d2eb8e2386a00a201d3a74ee4092e5ed`; archive size was 9,146,039 bytes and its root `zizmor` entry was inspected.
- The initial repository scan failed with exit 13 on a medium, high-confidence `dependabot-cooldown` finding. Adding the documented seven-day cooldown cleared the finding; GitHub documents that cooldown does not delay security updates.
- The final offline strict scan reported no findings, with one online-only audit suppressed, and exited 0.
- A non-repository fixture expanding `github.event.issue.title` directly inside `run` failed with exit 14 and a high-confidence, high-severity `template-injection` finding on the exact line.
- Prek configuration validation passed. Repeated full-file runs reported nine applicable hooks passed, two hooks not applicable, and zizmor completing in 0.07–0.09 seconds.
- `task verify`: pass; 19 tests ran, 18 passed, and the real-symlink test skipped because this Windows session lacks symlink privilege.
- Repository audit: pass; 50 files and 50 local links checked, policy SHA-256 `f16a088423a3210a86a44a90539ca0d8ea6b06680ee470feb69baa3e7baf9fa7`, and zero findings.
- actionlint v1.7.12 and both Git diff whitespace checks: pass.

## Initial GitHub-hosted evidence

- Workflow lint passed on Ubuntu. The retained `prek.log` records zizmor v1.30.0 scanning `.github/dependabot.yml` and both workflow files in 0.05 seconds, with no active findings and one online-only audit suppressed.
- The same log records valid prek configuration plus passing action-validator and pinact hooks. The retained `actionlint.log` records actionlint v1.7.12, two workflow files checked, and `status=pass`.
- Ubuntu 24.04 and Windows 2025 each ran all 19 regression tests with no skips or failures.
- Both audit artifacts report `status=pass`, 50 files checked, 50 local links checked, policy SHA-256 `f16a088423a3210a86a44a90539ca0d8ea6b06680ee470feb69baa3e7baf9fa7`, and zero findings.
- The pull-request audit revision is GitHub's synthetic merge commit `ad987898fc4acb8471a84d3ce1109cd593f813db`; run metadata identifies source commit `0a5414652b2151114b398d59f637ac592c715154`.

## Boundary

The automatic gate is read-only, offline, and uses the regular persona. It does not perform online metadata audits, prove Action SHA provenance, inspect repository settings, scan application dependencies, upload SARIF, mutate workflows, use API tokens, add a CI job, invoke an agent, or require Docker.
