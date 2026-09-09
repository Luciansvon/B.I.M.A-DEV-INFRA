# Bounded agent packet contract

## Identity and purpose

Name: `bima-agent-packet.v1`. Stability: **experimental**. The packet is a small, deterministic routing artifact produced only when canonical repository-audit evidence has status `fail` or `error`. It is not a prompt, an instruction, or authorization to invoke an agent.

Implementation: [`automation/agent_packet.py`](../../automation/agent_packet.py). Schema: [`schemas/bima-agent-packet.v1.schema.json`](../../schemas/bima-agent-packet.v1.schema.json).

## Input and command

`task agent-packet` reads `.artifacts/evidence/canonical.json` and reserves `.artifacts/agent/` for its outputs. Direct use:

```powershell
python -I automation/agent_packet.py --input .artifacts/evidence/canonical.json --output .artifacts/agent
```

The input must be a regular, non-symlink file no larger than 1 MiB. It must be the exact deterministic UTF-8/LF serialization of the current repository-audit adapter for `bima-evidence.v1`. Duplicate JSON keys, non-finite numbers, extra fields, inconsistent status/counts, and other modules fail closed. No network, credential, container, model, or third-party Python package is required.

## Routing

```text
canonical pass  --> no packet
canonical fail  --> route=machine  (known deterministic findings)
canonical error --> route=agent    (unclassified audit error)
```

`route=agent` means only that later orchestration may consider escalation. It grants no permission, performs no retry, and starts no model or external process. Finding text and paths are untrusted data; consumers must never execute or obey them as instructions.

## Output

Non-pass evidence produces:

- `packet.json`: deterministic `bima-agent-packet.v1` data;
- `packet.sha256`: SHA-256 of the exact packet bytes.

The packet records status, stage, audited commit/dirty state, route and reason, unique error codes and affected paths, the SHA-256 of the exact canonical input, total findings, and bounded finding excerpts. It deliberately excludes timestamps, runner details, raw logs, prompts, credentials, and inferred changed-file lists.

At most 20 evidence entries, 20 error codes, and 20 affected paths are retained. Codes are capped at 64 characters; paths/messages at 512. `evidence_truncated` is true when entries or strings are cut. `repeatable` remains `null` until measured and `retries` remains `0` because v1 performs no retries.

## Failure and cleanup

- Exit `0`, `not-needed`: valid pass evidence; owned stale packet files are removed.
- Exit `0`, `generated`: valid fail/error evidence; packet and hash are written. The upstream audit still owns the workflow failure status.
- Exit `2`: invalid/unreadable input or output; diagnostics are sanitized and owned stale packet files are removed when the output directory is usable.

The adapter does not generalize build, test, benchmark, release, or deployment failures. New stages require explicit mappings and compatibility evidence rather than overloading this repository-audit contract.

## GitHub adapter

Existing CI and reusable repository-audit jobs call the generator after canonicalization with `if: !cancelled()`. They add optional packet paths to the existing 14-day evidence artifact. No job, permission, token, service, or agent invocation is added. A passing run intentionally has no packet files.
