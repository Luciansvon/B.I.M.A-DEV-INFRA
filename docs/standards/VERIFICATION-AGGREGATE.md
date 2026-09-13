# Verification aggregate v1

Status: **Executable deterministic core; no project command execution.**

## Purpose

`verification_aggregate.py` converts a fixed verification plan plus one or
more `bima-verification-result.v2` records into one fail-closed aggregate
verdict. This closes the gap between individual test evidence and a meaningful
required-scope status without adding a provider, model, retry, or consumer pin.

```text
verification plan
        +
bounded v2 results
        |
        v
PASS | FAIL | UNKNOWN | BLOCKED
        +
aggregate.json
```

## Inputs

`bima-verification-plan.v1` declares:

- aggregate, project, repository, exact subject, and exact policy identity;
- a non-empty sorted set of required check IDs;
- a disjoint sorted set of optional check IDs.

The CLI accepts 0–64 result files so complete evidence absence becomes an
explicit `UNKNOWN`, not a parser failure. Each input is strict UTF-8 JSON of at most
1 MiB; symbolic-link inputs are rejected. Results must use
`bima-verification-result.v2`, match the declared
project and policy, share one exact subject revision/dirty state, and use the
declared applicability. Duplicate, undeclared, cross-subject, cross-policy,
malformed, or unsupported results fail as contract errors.

The current input result schema supports `rust-libtest-text.v1`. Adding another
adapter requires its own reviewed result contract; the aggregator does not
pretend arbitrary output is valid evidence.

The strict v2 validator is shared with the known-failure classifier through
`verification_result_contract.py`, so both capabilities reject the same
malformed result instead of maintaining divergent copies of the contract.

## Deterministic verdict

For required checks, precedence is:

1. `FAIL` when at least one valid required result is `FAIL`;
2. otherwise `BLOCKED` when at least one required result is `BLOCKED`;
3. otherwise `UNKNOWN` when required evidence is missing;
4. otherwise `UNKNOWN` when a required result is `UNKNOWN`;
5. otherwise `UNKNOWN` when a required result is marked flaky;
6. otherwise `PASS` when every required check has valid `PASS` evidence.

Optional missing, non-pass, or flaky results remain visible in
`optional_non_pass` and counts but do not alter a complete required-scope
`PASS`. All unresolved required IDs remain visible even when a higher-priority
verdict wins.

## Output and evidence

`aggregate.json` uses `bima-verification-aggregate.v1` and records:

- aggregate verdict and reason code;
- project, subject, and policy identity;
- canonical verification-plan SHA-256;
- every declared check, including missing ones;
- canonical SHA-256 for every reported result;
- required/optional counts and unresolved IDs.

Exit codes are `0=PASS`, `1=FAIL`, `2=UNKNOWN/contract error`, and
`3=BLOCKED`. A successful parser invocation does not override its aggregate
verdict.

## Permissions, limits, and security

- Python 3.11+ standard library only.
- Read-only access to declared plan/result files.
- Write access only to the selected output directory.
- No network, credentials, shell command, subprocess, retry, model call, or
  publication.
- Output directory symlinks are rejected; the owned `aggregate.json` is
  replaced deterministically.

This verifier aggregates evidence; it does not authorize execution or prove
the producer is trusted. A protected runner must still establish result origin
and preserve native evidence.

## Compatibility

The contract is additive. It does not modify v1 evidence, v1 agent packets,
v2 result bytes, consumer pins, or Policy Gate authorization. Future retry
groups, waivers, non-test adapters, or release gating require versioned
extensions and compatibility evidence.

## CLI

```text
python -I automation/verification_aggregate.py \
  --plan <bima-verification-plan.v1.json> \
  --result <bima-verification-result.v2.json> \
  --result <another-result.json> \
  --output <trusted-output-directory>
```
