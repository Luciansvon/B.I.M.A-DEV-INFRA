# Prek pre-flight validation — 2026-09-09

## Verdict

The bounded local Windows integration passed. Hosted evidence is pending and must pass before this increment is merged or described as fully validated.

## Source

- Base revision: `768c6ae722fd9b6cc5a7b0b38b55bd16168f2bef`.
- Branch: `codex/cost-aware-p0-prek`.
- Pull request and hosted run: pending.

## Local Windows evidence

- prek v0.5.2 Windows amd64 archive SHA-256 matched `03b6a7261d3a7e2d184ceca9c7e5fcb43b9dec83c8945976cddc3caa8b34b4c0`.
- The Linux amd64 archive used by CI matched SHA-256 `a4d51a463cb15ee2929368cc4884eec4ef33dce3ff5101b40e8ad7e1205b8f40`; its nested archive layout was inspected before finalizing extraction.
- `prek validate-config prek.toml`: pass.
- Full-file pre-flight after staging the complete change: six applicable hooks passed in 199 ms; two hooks skipped because the tree had no illegal Windows filenames or new submodules.
- `task verify`: pass; 19 tests ran, 18 passed, and the real-symlink test skipped because this Windows session lacks symlink privilege.
- Repository audit: pass; 41 files checked and zero findings.
- actionlint v1.7.12 and both Git diff whitespace checks: pass.

## Scope and limitations

The hook set is non-mutating and uses only prek's bundled implementations. It adds early checks for path portability, TOML/YAML syntax, mixed line endings, conflict markers, common private-key headers, and new submodules. It intentionally does not duplicate JSON, size, symlink, test, repository-audit, or workflow-semantic checks.

The private-key detector is heuristic, skipped hooks mean not applicable rather than independently passed behavior, and local Windows execution is not hosted proof. Docker, remote hook environments, automatic formatting, release actions, and agent invocation are absent.
