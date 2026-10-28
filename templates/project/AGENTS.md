# AGENTS.md

## Scope

This file governs work in `__PROJECT_NAME__`. Application behavior and project decisions stay in this repository; shared workflows and global standards stay in B.I.M.A-DEV-INFRA.

## Before changing code

1. Read `README.md`, `ARCHITECTURE.md` and the relevant incidents.
2. Identify the build, test and release commands that the change affects.
3. Check whether the change alters a shared workflow contract.

## Rules

- Run the project's build and tests before claiming a change works.
- Keep the repository audit passing; do not weaken `.bima/audit.json` to hide a missing file.
- Do not commit secrets, production data or unrelated binaries.
- Record a project incident when a failure has a confirmed root cause; promote it only when the shared criteria apply.

## Evidence

Every non-trivial change leaves a test result, workflow run, artifact, benchmark or log. A green claim without one is not evidence.
