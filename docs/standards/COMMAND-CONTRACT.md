# Deterministic command contract

## Identity

Name: `Taskfile.yml`. Stability: **experimental**. Purpose: give humans, CI, and agents the same explicit commands for work that does not require model reasoning.

## Commands

| Command | Requires | Output/evidence | Failure |
|---|---|---|---|
| `task test` | Python 3.11+ | unittest console output; CI preserves `tests.log` | any failed/error test or timeout |
| `task audit` | Python 3.11+, Git | `.artifacts/audit/result.json` and `report.md` | audit finding, configuration error, or timeout |
| `task workflow-lint` | actionlint 1.7.12 | version and findings; CI preserves `actionlint.log` | lint finding, missing tool, or timeout |
| `task check` | dependencies above | combined command results | any component fails |
| `task diff-check` | Git | command status | staged or unstaged whitespace error |
| `task verify` | dependencies above | full current verification result | check or diff-check fails |

`task build` and `task nightly` are absent until a project-agnostic implementation and evidence contract exist. A placeholder success would be a false green.

## Configuration

The contract accepts only tool/path overrides:

- `PYTHON`, default `python`;
- `ACTIONLINT`, default `actionlint`;
- `EVIDENCE_DIR`, default `.artifacts`.

These overrides select installed tools and the evidence location; they do not execute caller-provided project commands.

## GitHub adapter

GitHub Actions installs Task v3.53.1 with the upstream archive checksum, then calls the same `task test`, `task audit`, and `task workflow-lint` entry points. The workflow retains its Ubuntu/Windows audit matrix and existing evidence artifacts. The adapter handles setup and upload; Task owns the deterministic command contract.

## Local use

Install the pinned Task release and actionlint version, then run `task verify`. Python-only checks remain directly runnable when Task/actionlint are absent. A local pass is not hosted CI proof.

## Security and compatibility

Task setup is pinned to a full Action commit and verifies the selected Task archive checksum. Tool updates require checksum review, local parsing/execution, actionlint, repository audit, and hosted evidence. This first increment does not add hooks, automatic fixes, downloads from Task commands, release side effects, or agent invocation.
