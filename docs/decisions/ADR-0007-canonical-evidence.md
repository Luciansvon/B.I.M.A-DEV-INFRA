# ADR-0007 — Separate canonical results from execution metadata

Status: Accepted as experimental; hosted validation pending.
Date: 2026-09-09.

## Context

Issue [#3](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3) requires semantic evidence rather than byte-identical raw reports. Current repository-audit results include timestamps and can use platform-native line endings, so hashing raw files produces false mismatches even when status, policy, toolchain, counters, and findings agree.

## Decision

Introduce JSON Schema Draft 2020-12 contracts for `bima-evidence.v1` and separate `bima-evidence.execution.v1` metadata. Implement the first adapter for repository-audit version 1 using Python's standard library. Hash deterministic UTF-8/LF canonical bytes and retain the raw source hash, timestamp, and runtime only in execution metadata.

## Alternatives considered

- Compare raw result hashes: rejected because timestamps and platform formatting are intentionally volatile.
- Delete all provenance metadata: rejected because raw digest and runtime remain useful for debugging and audit trails.
- Claim full RFC 8785 JSON Canonicalization Scheme compliance: rejected because v1 needs only a constrained no-float data model, and an additional implementation dependency would add no measured value here.
- Add a cross-job aggregation job: deferred because each existing matrix artifact can carry comparable canonical evidence without another runner allocation or artifact download.

## Consequences

Ubuntu and Windows results can be compared by one recorded SHA-256 while preserving execution-specific evidence separately. The schema is shared, but only the repository-audit adapter exists; build, benchmark, and security modules are not automatically covered. Serializer or field-semantics changes can alter hashes and therefore require versioned migration evidence.

## Evidence

- [Canonical evidence contract](../standards/EVIDENCE-CONTRACT.md)
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)
- [RFC 8785 JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785.html)
- [SLSA provenance model](https://slsa.dev/spec/v1.2/provenance)

## Supersedes / Superseded by

None.
