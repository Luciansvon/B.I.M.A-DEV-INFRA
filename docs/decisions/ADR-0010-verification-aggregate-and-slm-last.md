# ADR-0010 — Aggregate verification now; SLM last

Status: **Accepted.**
Date: 2026-09-13.
Decision owner: Bima; Solo implementation.

## Context

The capability architecture defines deterministic aggregation for a fixed
required-check set, but `main` previously emitted only individual v2 results.
Waiting for a new consumer would leave this central fail-closed rule as design
text even though it can be implemented and tested safely inside DEV-INFRA.

The local SLM remains data-, benchmark-, hardware-, and consumer-dependent. It
does not improve execution authority or evidence truth and must not delay
deterministic capabilities that already have stable contracts.

## Decision

1. Implement `bima-verification-plan.v1` and
   `bima-verification-aggregate.v1` as additive, provider-neutral contracts.
2. Aggregate already-normalized evidence only. Do not execute project commands,
   authorize retries, mutate consumer pins, or call a model.
3. Apply the accepted precedence `FAIL`, then `BLOCKED`, then `UNKNOWN`, then
   complete `PASS`; retain all unresolved and optional non-pass checks.
4. Continue deterministic shared-infrastructure implementation when its trust
   boundary and verification are clear; do not invent consumer adoption merely
   to obtain evidence.
5. Move local SLM implementation to the final roadmap stage. Reconsider it only
   after the deterministic control plane, real operational adapters, Failure
   Memory baseline, and relevant consumer evidence are mature. Its existing
   benchmark and safety gates remain minimum requirements, not a delivery
   deadline.

## Consequences

DEV-INFRA gains a meaningful required-scope verdict without expanding command
execution or permissions. Missing results and flaky required checks cannot
become green. Optional failures remain visible. The first hosted proof can use
the existing real-format Rust fixture without changing AI-COLOR-COMPARE.

This decision changes roadmap order, not SLM safety thresholds. It does not
claim that arbitrary application build/test commands, sandboxes, ReleaseProof,
or model runtime are implemented.

## Evidence

- [Capability result and aggregation rules](../architecture/CAPABILITY-CONTRACT.md#4-result-axes-and-aggregation)
- [Verification aggregate contract](../standards/VERIFICATION-AGGREGATE.md)
- Hosted validation is recorded in the corresponding implementation audit.
