# Pinact integration validation — 2026-09-09

## Verdict

Local Windows validation passed. Hosted evidence is pending and must pass before this increment is merged or described as fully validated.

## Source

- Base revision: `1a746da69bfd2ace21c5aef46b8a4b7b669e4fd8`.
- Branch: `codex/cost-aware-p0-pinact`.
- Pull request and hosted run: pending.

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

## Boundary

The automatic gate is read-only and offline. It does not verify version comments, SHA ownership/provenance, or minimum release age. Docker, automatic pin updates, API tokens, a new CI job, release side effects, and agent invocation are absent.
