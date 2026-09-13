# Verification aggregate v1 validation — 2026-09-13

## Verdict

Local and hosted implementation evidence is `PASS`. The additive aggregator
applies the architecture's fixed required-check precedence without
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
actionlint, action-validator, pinact, zizmor, and prek are `NOT RUN`. Their
reviewed pinned versions passed in the hosted workflow-lint job.

## Hosted evidence

- PR #31 code revision:
  `97e41bb24ddfcd0d34ccaca2ff5034297fb28a2c`.
- Infrastructure CI run [`34753773782`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34753773782): workflow lint, Ubuntu 24.04, and Windows 2025 passed.
- Both inspected aggregate artifacts report `PASS`,
  `ALL_REQUIRED_CHECKS_PASSED`, required `1/1`, and zero unresolved required
  checks for pull-request merge subject
  `a01c4e17446bb142150e332cb47d82829e193e76`.
- Both plans have canonical SHA-256
  `5fcef394468b4784979a3f8a480cddfd8a0135a1901321298be997abd67c4504`.
  Result digests differ because attempt IDs are platform-specific; aggregate
  semantics match.
- Ubuntu and Windows each ran `127` tests. Both repository-audit artifacts
  report `PASS`, `158` files, `181` local links, and zero findings.
- Trusted launcher run [`34753773924`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34753773924) returned `ALLOW`,
  `MATCHED_REPOSITORY_AUDIT_RULE`, and `verifier_launched=true`.

## Boundary

This is a result verifier, not an executor or Policy Gate expansion. It does
not make arbitrary project commands safe to run. Policy Gate v1 still
authorizes only `repository-audit.v1`; SLM implementation is moved to the final
roadmap stage under ADR-0010.
