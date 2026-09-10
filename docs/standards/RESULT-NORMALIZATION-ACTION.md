# Rust result normalization action v1

Status: **Beta shared composite action; real-consumer opt-in pending.**

## Identity and purpose

`.github/actions/normalize-rust-libtest/action.yml` converts an already-produced bounded Rust libtest log into `bima-verification-result.v2`. It does not execute the project command, retry, repair, publish, use credentials or call a model.

The caller owns test execution and supplies a strict `bima-normalization-config.v1` file. The action binds runtime subject, attempt and exit-code identity to that config and the actual source bytes before calling the shared normalizer.

## Inputs

| Input | Required | Default | Description |
|---|---:|---|---|
| `config-path` | yes | — | Project-owned v1 normalization config |
| `native-output-path` | yes | — | Bounded UTF-8 Rust output, maximum 1 MiB |
| `failure-log-path` | no | empty | Optional bounded same-attempt TypeScript diagnostic log |
| `subject-revision` | yes | — | Full tested Git SHA |
| `subject-dirty` | no | `false` | Tested worktree cleanliness |
| `attempt-id` | yes | — | Provider attempt identity |
| `attempt-sequence` | no | `1` | One-based attempt number |
| `exit-code` | yes | — | Preserved native command exit code |
| `output-directory` | yes | — | Trusted destination for `result.json` |

The config declares project/check identity, required status, expected test count, adapter, exact command text, policy revision, source environment and equivalence key. The command digest is SHA-256 of the UTF-8 command text. The policy digest is SHA-256 of canonical config bytes, so formatting changes do not alter policy identity.

## Outputs and evidence

| Output | Description |
|---|---|
| `verdict` | `PASS`, `FAIL`, `UNKNOWN` or `BLOCKED` |
| `reason-code` | Deterministic outcome reason |
| `result-sha256` | SHA-256 of canonical `result.json` bytes |

The caller retains `result.json` and the approved native log as artifacts. A successful action step is not independently a PASS claim; consumers inspect the verdict and required evidence.

## Runner, permissions and limits

- GitHub-hosted Linux or Windows with Bash and Python 3.13;
- no `GITHUB_TOKEN` permission or external credential required by the action;
- no network access performed by the action;
- one result per invocation, two source files maximum, 1 MiB per input;
- no concurrency or retry behavior; the caller owns both;
- expected runtime is below one minute after source production.

## Failure and security contract

`PASS` exits `0`, native `FAIL` exits `1`, and `UNKNOWN` or invalid input exits `2`. The action still emits outputs when a valid non-PASS result exists. Paths and scalar inputs enter the shell only through environment variables. Strict JSON, hashes, exact fields, bounded files and runtime identity validation fail closed.

Untrusted project content cannot gain execution through this action because the declared command is hashed but never executed. A caller that runs a different command creates misleading evidence; review and the caller's protected workflow remain the trust boundary.

## Compatibility and rollback

This interface is additive. It does not change `bima-evidence.v1`, `bima-agent-packet.v1` or the repository-audit workflow. Consumers opt in by pinning this action to a reviewed full DEV-INFRA SHA. Rollback removes the optional action invocation or restores the prior project commit; the independent v1 audit pin and artifacts remain valid.
