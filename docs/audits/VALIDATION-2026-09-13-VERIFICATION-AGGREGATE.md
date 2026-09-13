# Verification aggregate v1 validation — 2026-09-13

## Verdict

Local implementation is `PASS`; hosted evidence is pending. The additive
aggregator applies the architecture's fixed required-check precedence without
executing project commands, changing consumer pins, authorizing retry, or
calling a model.

Starting `main` revision:
`bb5a7f7072e5294557798813081544aee492ddfc`.

## Implemented contract

- `bima-verification-plan.v1` binds aggregate, project, exact subject, exact
  policy, and sorted disjoint required/optional check IDs.
- `bima-verification-aggregate.v1` retains every declared check, canonical
  plan/result digests, counts, unresolved required IDs, and optional non-pass
  IDs.
- Required verdict precedence is `FAIL`, `BLOCKED`, `UNKNOWN`, then complete
  `PASS`.
- Zero input results produce `UNKNOWN: REQUIRED_EVIDENCE_MISSING` rather than
  an empty green result.
- The aggregator and known-failure classifier reuse one strict v2 result
  validator, preventing duplicate validation rules from drifting apart.

## Local evidence

- Focused aggregate suite: `16` tests passed in `0.719` seconds.
- Existing known-failure classifier regression after validator reuse: `11`
  tests passed in `0.348` seconds.
- Full regression: `127` tests, `1` skipped, `0` failed in `78.951` seconds.
  The skip is the existing Windows symlink-privilege boundary.
- Workflow-shaped normalization plus aggregation fixture: `PASS`,
  `ALL_REQUIRED_CHECKS_PASSED`, required `1/1`.
- Repository audit: `PASS`; `158` files checked and `0` findings.
- Negative coverage includes failed, blocked, unknown, flaky, missing,
  optional non-pass, duplicate, undeclared, cross-subject, cross-project,
  cross-policy, wrong-applicability, malformed, duplicate-key, and non-finite
  inputs.

Local Task/pre-flight binaries are not installed on this machine, so local
actionlint, action-validator, pinact, zizmor, and prek are `NOT RUN`. The
workflow installs their reviewed pinned versions; hosted workflow/security
evidence must be inspected before final completion.

## Hosted evidence

Pending pull-request Ubuntu 24.04 and Windows 2025 artifacts. Do not treat this
section as hosted `PASS` until run IDs and inspected aggregate outputs are
recorded.

## Boundary

This is a result verifier, not an executor or Policy Gate expansion. It does
not make arbitrary project commands safe to run. Policy Gate v1 still
authorizes only `repository-audit.v1`; SLM implementation is moved to the final
roadmap stage under ADR-0010.
