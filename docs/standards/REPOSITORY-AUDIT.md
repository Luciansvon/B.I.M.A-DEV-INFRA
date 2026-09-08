# Repository audit contract

## Identity and purpose

Name: `repository-audit`. Stability: **experimental**. Implements the existing shared execution/evidence architecture for inexpensive, offline repository hygiene. It does not implement application builds, release gates, benchmarks, or general security scanning.

Implementation: [`automation/repository_audit.py`](../../automation/repository_audit.py). Reusable entry point: [workflow](../../.github/workflows/repository-audit.yml). No third-party Python packages.

## Inputs

| Workflow input | Required | Type | Default | Meaning |
|---|---|---|---|---|
| `infra-ref` | yes | string | none | Full lowercase 40-character DEV-INFRA commit SHA; use the same SHA as the workflow call |
| `policy-path` | no | string | empty | POSIX path relative to caller Git root; empty means built-in defaults |
| `artifact-name` | no | string | `repository-audit` | Unique artifact prefix per call, including matrix invocations |

No secrets or arbitrary executable command inputs. Caller must allow `contents: read`.

CLI inputs: `--root` is a Git top-level working tree with a HEAD commit; `--policy` is the same optional relative path; `--output` is a trusted writable directory reserved for evidence. Use a fresh directory outside the target checkout for untrusted repositories. For local development this repo ignores `.artifacts/`.

```powershell
python -I automation/repository_audit.py --root . --policy .bima/audit.json --output .artifacts/audit
python -I -m unittest discover -s tests -v
```

Policy JSON has exactly these fields:

```json
{
  "schema_version": 1,
  "required_files": ["README.md", "AGENTS.md"],
  "max_file_bytes": 1048576
}
```

These are also the built-in defaults. Policy is at most 64 KiB. `required_files` has 1–100 unique safe repository-relative paths. `max_file_bytes` is an integer from 1 through 10,485,760. Unknown fields, duplicate JSON keys, non-finite numbers, booleans in integer fields, unsupported versions, and absent explicitly supplied policies fail closed. Symlinks, junctions, absolute paths, Git internals, and traversal are rejected for policy/required paths.

## Checks and boundaries

Inventory is Git-tracked files plus non-ignored untracked files. This includes new local changes; CI checks the checked-out event revision, normally the merge revision for a pull request. Ignored generated output is not scanned, and ignored files cannot satisfy requirements or link checks. A repository with over 100,000 inventory entries is rejected.

Checks:

1. Required files exist, are nonempty, and appear in the inventory.
2. Files are regular, readable, and within the byte budget. Symlinks, junctions, and submodules fail rather than being followed.
3. `.json` files are strict JSON, without duplicate keys or non-finite literals.
4. Supported inline Markdown links and images resolve to inventory files/directories within the repository. URI-encoded paths, angle-bracket paths, root-relative paths, and ordinary parent-directory links are supported. Fenced/indented code and basic inline code are skipped.

Markdown support is intentionally partial: reference-style links, multiline syntax, nested parentheses/brackets, HTML, and heading anchors are not fully validated. External URLs and URI schemes are skipped without network requests. This is not a complete CommonMark parser or an external-link availability check. Policy can select required documents but does not silently execute their instructions.

## Outputs and evidence

Workflow output `artifact-id` identifies the uploaded artifact on successful completion. On failure, use the workflow run's artifact list; downstream workflow outputs should not be relied on for failed jobs.

`result.json` version 1 contains:

| Field | Meaning |
|---|---|
| `schema_version`, `module` | Integer `1`, string `repository-audit` |
| `status` | `pass`, `fail`, or `error` |
| `generated_at` | UTC ISO 8601 timestamp |
| `validator_sha256`, `python_version` | Hash of executed validator bytes and actual Python version |
| `revision`, `dirty` | Audited HEAD and working-tree dirty flag; null if unavailable |
| `policy_sha256` | Hash of exact policy bytes; null for built-in defaults or unavailable policy |
| `files_checked`, `local_links_checked` | Actual counters, not claimed test coverage |
| `findings` | Array of objects with `code`, repository-relative `path`, nullable `line`, and `message` |

`report.md` is a human-readable rendering of the result. Reports never include input document bodies. Paths/messages are escaped for Markdown/HTML display. Findings have no auto-fix side effects.

## Failure contract

- Exit `0`: checks completed with no findings.
- Exit `1`: checks completed with findings (missing file, size budget, malformed JSON, unsupported file, bad local link).
- Exit `2`: root/Git/policy configuration prevents the audit.
- Pass/fail/error audit outcomes all produce reports. An invalid CLI, unwritable output, cancelled job, checkout/setup failure, or process kill may prevent reports; CI must not treat missing reports as success.
- No warning-only pass, automatic retries, or silent policy fallback.

## Runner, permissions, and limits

GitHub-hosted Ubuntu 24.04; Git, Bash, and pinned Python 3.13.15. No hardware/device requirements. `contents: read` only, no OIDC or external credentials. Ten-minute job timeout; individual Git commands time out at 30 seconds. Expected runtime: seconds for the script on a small documentation repository, plus hosted runner/setup/upload time.

The reusable workflow has no shared concurrency group that could cancel its caller. The caller owns cancellation. This repo's CI cancels outdated runs on the same workflow/ref and tests on Ubuntu/Windows. Branch pushes run through pull-request CI; direct `push` CI is limited to `main` to avoid duplicate branch and PR runs. Evidence retention is 14 days. Each invocation needs its own `artifact-name` to avoid upload collisions.

## Consuming from another repository

Publish and verify an infrastructure commit before use. Replace both `REVIEWED_INFRA_COMMIT_SHA` placeholders with the same real full SHA; this example is deliberately not a live published reference.

```yaml
name: Repository hygiene
on: [push, pull_request]
permissions:
  contents: read
jobs:
  audit:
    uses: Luciansvon/B.I.M.A-DEV-INFRA/.github/workflows/repository-audit.yml@REVIEWED_INFRA_COMMIT_SHA
    with:
      infra-ref: REVIEWED_INFRA_COMMIT_SHA
      policy-path: .bima/audit.json
      artifact-name: repository-hygiene
```

The second SHA is explicit because caller context/checkout does not identify the reusable workflow implementation. The workflow validates SHA syntax but does not prove the two pins match; code review must verify that pairing. Do not consume mutable branches for executable infrastructure.

## Compatibility and security

First experimental contract: no existing consumers to migrate. Input/status/policy changes require an ADR and updated regression fixtures. The result version is scoped to this module; it is not yet a universal benchmark/build schema.

Follow the [security baseline](SECURITY-BASELINE.md). The module treats the caller as data and never executes its scripts. This does not make a malicious infrastructure SHA safe: review the pinned implementation. Caller-owned policies and workflow pins require protected review. GitHub-hosted Actions support is targeted; GHES and self-hosted integration are unverified.
