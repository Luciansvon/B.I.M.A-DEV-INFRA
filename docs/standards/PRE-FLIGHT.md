# Pre-flight hook contract

## Identity

Name: `prek.toml`. Stability: **experimental**. Purpose: reject cheap, deterministic repository mistakes before they consume hosted CI or agent reasoning.

## Scope

Prek v0.5.2 runs bundled hooks plus one local system hook for action-validator v0.9.0. The configuration has no remote hook repositories, managed hook environments, containers, project-specific application commands, or automatic fixers.

The current hooks check:

- case-conflicting paths and filenames illegal on Windows;
- TOML and YAML syntax;
- mixed line endings without rewriting files;
- merge-conflict markers even outside an active merge;
- common private-key headers;
- newly added Git submodules.
- GitHub workflow and local Action schemas, including referenced path globs.

JSON validation, file-size limits, symlink policy, tests, and actionlint's syntax/expression checks remain owned by their existing commands. Action-validator adds schema and path-glob validation rather than replacing actionlint.

## Commands

- `task preflight` validates `prek.toml` and runs every hook against all tracked files.
- `prek install` installs the local Git hook. Normal commits then check staged files.
- `task check` and `task verify` include the full-file pre-flight.

## GitHub adapter and evidence

The existing workflow-lint job downloads the prek v0.5.2 and action-validator v0.9.0 Linux amd64 binaries, verifies their fixed SHA-256 digests, and calls `task preflight`. It preserves `.artifacts/prek.log` in the existing workflow-lint artifact, avoiding another runner job.

The job has `contents: read`, no secrets, a ten-minute timeout, and no publish side effects. Failure means invalid configuration or any failed hook. The private-key hook is heuristic and does not replace secret scanning.

## Compatibility

`prek.toml` is prek-specific and intentionally not compatible with Python `pre-commit`. Prek and action-validator are standalone tools; Docker is not required. Windows users install action-validator through Cargo or NPM because v0.9.0 has no official Windows release binary. Hook behavior and minimum supported versions are pinned together. A version update requires checksum review and local plus hosted evidence.
