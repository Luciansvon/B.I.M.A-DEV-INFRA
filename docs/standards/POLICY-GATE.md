# Policy Gate v1

Status: **Executable local contract; one operation supported.** This is not a general sandbox or release authority.

## Purpose

Policy Gate v1 binds a strict project declaration and operation request to an exact trusted policy hash before running the existing `repository-audit.v1` verifier. Unknown schemas, fields, operations, policies and resource requests fail closed.

```text
project.json + request.json
              |
trusted policy bytes + expected SHA-256 + trusted actor/time
              |
              v
       ALLOW or DENY decision.json
              |
       ALLOW only
              v
 reviewed repository-audit process -> result.json + report.md
```

## Inputs

| Input | Schema / source | Trust rule |
|---|---|---|
| Project declaration | `bima-project.v1` | Subject-controlled; may request only, never expand policy |
| Operation request | `bima-operation-request.v1` | Bound by canonical SHA-256 to the decision |
| Policy | `bima-policy.v1` | Bytes must match `--expected-policy-sha256` from a reviewed wrapper/base revision |
| Actor and validity window | Trusted executor arguments | Must not be copied from subject-controlled JSON |

JSON is UTF-8, duplicate-key and non-finite-number rejecting, size-bounded and exact-field validated. Paths are relative POSIX paths without traversal, Git internals, drive syntax, symlink or junction traversal.

The only supported operation is:

```text
operation_id: repository-audit
command_ref: repository-audit.v1
network destinations: none
credentials: none
attempts: explicitly bounded
timeout: explicitly bounded
output: one exact policy-approved repository-relative root
```

## Decision and enforcement

`bima-decision.v1` records the canonical request digest, exact policy revision/hash, rule IDs, reason code, obligations, budget, trusted actor and validity window. Initial decisions are `ALLOW` or `DENY`; `HUMAN_REQUIRED` is reserved in the schema for future consequential operation classes and is not emitted by this verifier-only implementation.

Immediately before execution, the executor verifies:

- policy bytes still match the trusted expected hash;
- project ID plus repository identity, operation, command, output, timeout, attempt, network and credential scopes match;
- checked-out `HEAD` equals the requested full revision;
- the subject worktree is clean;
- output containment does not traverse a symlink or junction.

An allowed audit runs as an argument-array subprocess with isolated Python mode and the authorized timeout. Exit code and required `result.json` status must agree. `decision.json`, `audit/result.json` and `audit/report.md` are the produced evidence. A denial writes only the decision and never launches the audit.

## Permissions and runner requirements

- Python 3.11+ standard library and Git.
- Read access to the subject repository and audit policy.
- Write access only to the declared output root.
- No network destination or credential is accepted by v1.
- The wrapper must obtain trusted policy bytes/hash, actor and time independently of the subject branch.

The local developer shell is not an OS sandbox. This module enforces its own dispatch contract, process timeout and output containment; a protected hosted wrapper must also restrict token permissions, filesystem/process access and network at the runner boundary. Do not use a subject-controlled expected hash or actor value as authoritative CI input.

## Failure conditions

| Condition | Result |
|---|---|
| Malformed/unknown contract | `ERROR`, exit 2, no operation |
| Valid request outside policy | `DENY`, exit 3, decision evidence only |
| Allowed audit reports findings | audit `fail`, exit 1 |
| Allowed audit cannot establish a result | audit `error`, exit 2 |
| Allowed audit passes | audit `pass`, exit 0 |

## Compatibility and migration

Policy Gate v1 does not modify `bima-evidence.v1`, `bima-evidence.execution.v1` or `bima-agent-packet.v1`. The existing repository-audit output bytes and meanings remain intact under the `audit/` subdirectory. Consumers do not change pins until a protected reusable-workflow wrapper and hosted compatibility evidence exist.

The checked-in positive/negative fixtures under `tests/fixtures/policy-gate/` prove the initial allow/deny contract. Unit tests also cover policy-hash tampering, resource elevation, output/timeout/attempt limits, request binding, unknown operations, wrong revisions and dirty subjects.

## CLI shape

```text
python -I automation/policy_gate.py \
  --root <subject-root> \
  --project <project.json> \
  --trusted-policy <policy.json> \
  --request <request.json> \
  --expected-policy-sha256 <trusted-64-hex-value> \
  --actor <trusted-actor> \
  --issued-at 2026-09-10T02:00:00Z \
  --expires-at 2026-09-10T02:05:00Z
```

The CLI deliberately has no shell-command input, generic provider selection, approval string, credential injection or network option.
