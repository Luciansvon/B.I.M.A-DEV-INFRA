# GitHub workflow schema validation contract

## Identity

Tool: action-validator v0.9.0. Stability: **experimental**. Purpose: detect malformed GitHub workflow/local Action structures and unmatched `paths` or `paths-ignore` globs before hosted execution.

## Selection and execution

The local prek hook selects tracked files matching:

```text
.github/workflows/*.yml
.github/workflows/*.yaml
.github/actions/**/action.yml
.github/actions/**/action.yaml
```

Prek passes selected filenames directly to `action-validator --verbose`. `task preflight`, local Git hooks installed with `prek install`, and GitHub CI therefore use the same configuration. Actionlint remains enabled because its expression and shell-aware checks are complementary rather than equivalent.

## Version and installation

GitHub downloads the official v0.9.0 Linux amd64 binary and verifies SHA-256 `9f42f94fca5b8d04c13bccfbb331104b37a9250650d89ae58dc888d46206f9b9` before execution. The binary is placed only in the ephemeral runner temporary directory.

The v0.9.0 release does not publish a Windows binary. Local Windows validation builds the pinned crates.io package with `cargo install action-validator --version 0.9.0 --locked`; the resulting executable is not committed. NPM is another upstream-supported installation path. Docker is not required.

## Evidence and failure

The existing workflow-lint job records the version, selected file type, hook result, and overall pre-flight status in `.artifacts/prek.log`. Any schema, YAML decoding, or matching path-glob error fails the hook and job. A clean result validates only the selected workflow/action files; it does not prove runtime behavior, permissions safety, shell correctness, or action supply-chain integrity.

## Security and compatibility

The job retains `contents: read`, receives no secrets, and adds no side effects. The upstream tool is GPL-3.0-only and runs as an external development/CI executable; its source is not copied into this repository. Version or schema behavior changes require local and hosted evidence before adoption.
