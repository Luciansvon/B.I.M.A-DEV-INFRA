# Project repository template

Status: **experimental**. Generates a starting scaffold; it does not provision GitHub settings, secrets or branch protection.

## Identity

`templates/project/` holds the scaffold and `automation/bootstrap_project.py` writes it into an empty target directory with one reviewed DEV-INFRA commit.

## Usage

```bash
python -I automation/bootstrap_project.py \
  --target ../my-project \
  --infra-ref <40-hex-dev-infra-sha> \
  --project-name "My Project"
```

The command prints a canonical JSON manifest with each file's path, byte count and SHA-256. It refuses a non-empty target, an invalid SHA, a symlinked template and any unresolved placeholder.

## Included files

| File | Purpose |
|---|---|
| `README.md` | Project identity, build/test commands, shared-infrastructure pin |
| `AGENTS.md` | Agent scope, required checks, evidence rule |
| `ARCHITECTURE.md` | Project architecture template |
| `INCIDENTS.md` | Project incident template |
| `.bima/audit.json` | Minimal repository audit policy (`README.md`, `AGENTS.md`) |
| `.github/workflows/bima-shared-audit.yml` | Pinned call to the reusable repository audit |

The workflow reference and `infra-ref` input are written to the same commit. Keep them equal when updating.

## Failure contract

- Invalid `infra-ref` or project name fails before writing.
- A non-empty target is untouched.
- Template symlinks, non-UTF-8 files and unknown placeholders fail before writing.
- A write failure removes the files created by that invocation.

## Boundaries

The template does not create a GitHub repository, enable Actions, configure branch protection or immutable releases, add secrets, choose a language toolchain, or prove that the generated project builds. Those stay project-owned and must be configured and verified separately.

## Self-test

`tests/test_project_template.py` bootstraps a temporary project, checks placeholder replacement, manifest hashes and the generated workflow call, and proves that invalid input and a non-empty target write nothing.
