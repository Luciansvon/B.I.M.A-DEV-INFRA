# ADR-0002 — GitHub-hosted Dagger core with platform release adapters

Status: Accepted for experimental hosted validation.
Date: 2026-09-08.

## Context

Repository audit, regression tests, and workflow lint currently run through GitHub workflow steps. The same checks should become reusable pipeline code without requiring Docker or Dagger installation on the maintainer's laptop. Azure authentication and four simultaneous CI providers would add operational cost before a demonstrated need exists.

## Decision

Use a pinned Dagger 1.0 beta engine on a GitHub-hosted Ubuntu runner. Expose repository audit, unit tests, workflow lint, and their combined execution through the root `bima-infra` module. Return evidence directories; keep GitHub publication, Windows signing, Play Store upload, Vercel deployment, and similar credentialed side effects outside the portable core.

Keep native execution temporarily as a comparison oracle. Dagger audit evidence must match native evidence for deterministic fields; timestamps are intentionally excluded. Azure Pipelines, GitLab CI, a local container runtime, and self-hosted runners remain deferred.

## Pinning

- Module engine: `v1.0.0-beta.11`.
- GitHub Action: `dagger/dagger-for-github` v8.4.1 at full commit `27b130bf0f79a7f6fbbbe0fbca6760dc9bb40a77`.
- Python base image: `python:3.13.15-bookworm` at OCI digest `sha256:933b46a028fd786c9c3d426ebabc237e29a15912231ea8de576e95f0e4f41a4c`. The full image supplies Git and curl without a mutable package-install step.
- actionlint: v1.7.12 archive with verified SHA-256.

Resolved Dagger dependencies and images belong in `dagger.lock`. Updates require explicit review and hosted validation.

## Consequences

The laptop can run the existing Python validator and tests without a container runtime, but cannot execute Dagger locally. GitHub Actions is the Dagger execution environment for this phase. A successful source review or local Python test does not prove that the beta Dagger module loads; hosted evidence is required.

## Evidence required before acceptance

- Dagger module loads on the pinned engine.
- `bima-infra ci` produces audit, test, actionlint, and summary evidence.
- Deterministic audit fields match a native run from the same checkout.
- Workflow artifacts remain available on component failure where execution reached evidence generation.

## Supersedes / Superseded by

None.
