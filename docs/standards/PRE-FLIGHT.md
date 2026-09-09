# Pre-flight hook contract

## Identity

Name: `prek.toml`. Stability: **experimental**. Purpose: reject cheap, deterministic repository mistakes before they consume hosted CI or agent reasoning.

## Scope

Prek v0.5.2 runs only its bundled hooks. The configuration has no remote hook repositories, runtime environments, containers, project-specific commands, or automatic fixers.

The current hooks check:

- case-conflicting paths and filenames illegal on Windows;
- TOML and YAML syntax;
- mixed line endings without rewriting files;
- merge-conflict markers even outside an active merge;
- common private-key headers;
- newly added Git submodules.

JSON validation, file-size limits, symlink policy, tests, and GitHub workflow semantics remain owned by the existing audit, test, and actionlint commands. Prek does not duplicate those checks.

## Commands

- `task preflight` validates `prek.toml` and runs every hook against all tracked files.
- `prek install` installs the local Git hook. Normal commits then check staged files.
- `task check` and `task verify` include the full-file pre-flight.

## GitHub adapter and evidence

The existing workflow-lint job downloads the prek v0.5.2 Linux amd64 archive, verifies SHA-256 `a4d51a463cb15ee2929368cc4884eec4ef33dce3ff5101b40e8ad7e1205b8f40`, and calls `task preflight`. It preserves `.artifacts/prek.log` in the existing workflow-lint artifact, avoiding another runner job.

The job has `contents: read`, no secrets, a ten-minute timeout, and no publish side effects. Failure means invalid configuration or any failed hook. The private-key hook is heuristic and does not replace secret scanning.

## Compatibility

`prek.toml` is prek-specific and intentionally not compatible with Python `pre-commit`. Prek is a single binary; Docker is not required. Hook behavior and minimum supported version are pinned together. A version update requires checksum review and local plus hosted evidence.
