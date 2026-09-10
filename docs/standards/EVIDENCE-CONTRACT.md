# Canonical evidence contract

## Identity

Name: `bima-evidence.v1`. Stability: **experimental**. Purpose: make semantic results comparable across local, Ubuntu, and Windows execution without pretending volatile runner metadata is identical.

Schemas:

- [`bima-evidence.v1.schema.json`](../../schemas/bima-evidence.v1.schema.json)
- [`bima-evidence.execution.v1.schema.json`](../../schemas/bima-evidence.execution.v1.schema.json)

The schemas declare JSON Schema Draft 2020-12. The first implemented adapter accepts repository-audit result version 1 only.

## Inputs

`automation/canonical_evidence.py` accepts a regular UTF-8 `result.json` of at most 1 MiB. It rejects duplicate keys, non-finite numbers, unknown or missing fields, invalid hashes/revisions, boolean counters, malformed findings, and inconsistent status/finding combinations.

```text
python -I automation/canonical_evidence.py \
  --input .artifacts/audit/result.json \
  --output .artifacts/evidence
```

The input path and output directory are trusted infrastructure arguments; they are not project command inputs.

## Canonical output

`canonical.json` contains only comparison-relevant data:

- schema and overall status;
- subject revision and dirty state;
- exact policy SHA-256;
- Python version plus canonicalizer and validator SHA-256 values;
- ordered checks, metrics, and normalized findings.

Objects are serialized with sorted keys, two-space indentation, ASCII escaping, UTF-8 bytes, and LF termination. Findings are sorted by code, path, line, and message. The payload currently contains only strings, integers, booleans, nulls, arrays, and objects; floating-point values are forbidden. `canonical.sha256` hashes the exact `canonical.json` bytes.

This bounded serializer is deterministic for the v1 data model but is **not** claimed as a complete RFC 8785 implementation. Adding floating-point or broader JSON values requires a new reviewed canonicalization decision.

## Execution output

`execution.json` is deliberately excluded from canonical comparison. It records:

- canonical filename and SHA-256;
- source result filename, generation timestamp, and exact raw SHA-256;
- operating system, machine architecture, and actual Python runtime.

Raw source hashes may differ across executions because the module result contains a timestamp. That difference does not invalidate matching canonical hashes.

## Equivalence rule

Two executions are semantically equal only when their `canonical.json` bytes or `canonical.sha256` values match. A match covers the recorded revision, dirty state, policy, toolchain, status, metrics, and findings. It does not prove that unrecorded environment properties are equal or that the execution platform is trustworthy.

Dirty and clean subjects intentionally do not compare equal. Cross-platform comparison should use the same committed revision, policy bytes, Python version, validator bytes, and canonicalizer bytes.

## GitHub adapter and evidence

The repository CI runs `task evidence` after each Ubuntu/Windows audit. The reusable repository-audit workflow runs the same Python adapter directly after auditing the caller. Existing artifacts retain the raw result/report and add:

```text
evidence/canonical.json
evidence/canonical.sha256
evidence/execution.json
```

No new runner job, network request, secret, write permission, publish side effect, or external Python dependency is introduced.

## Failure and compatibility

Successful normalization exits 0 even when the source audit status is `fail` or `error`; the audit step remains responsible for failing the workflow. Invalid or unreadable input exits 2 without echoing input content and removes the three owned output filenames so stale evidence cannot masquerade as the current result. Evidence upload fails when required files are missing.

Future module adapters may add check shapes only through a compatible schema revision and regression evidence. Breaking field meaning, canonical serialization, or equivalence rules requires a new schema version and ADR.

## Accepted target architecture

[ADR-0009](../decisions/ADR-0009-capability-verification-architecture.md) defines the next architecture without changing this v1 contract. [CAPABILITY-CONTRACT](../architecture/CAPABILITY-CONTRACT.md) specifies separate execution, outcome, stability and authorization axes and the future v2 migration gates. Until that migration is implemented and validated, v1 readers continue to accept only the existing `pass`, `fail` and `error` statuses and current fields. Do not insert target-design fields into deployed v1 evidence.
