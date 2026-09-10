# Known failure registry v1

Status: **Executable exact-match classifier with DEV-INFRA hosted regression; consumer integration pending.**

## Purpose

`known_failure_registry.py` determines whether one canonical `bima-verification-result.v2` failure exactly matches a reviewed, time-bounded registry entry. It classifies routing only. It does not change the underlying `FAIL`, mark a test flaky, execute a remedy or authorize a retry.

## Required entry fields

Every `bima-known-failure-registry.v1` entry requires:

- stable entry ID;
- owner and reviewer;
- reason and retained issue/evidence reference;
- whole-second UTC `created_at` and `expires_at`, with a maximum 90-day validity;
- exact project, repository, check, cleanliness state, adapter, command digest, policy digest, environment, equivalence key and expected test count;
- exact failure reason code;
- one to 50 unique, sorted diagnostic signatures.

Each diagnostic signature binds tool, code, repository-relative path and SHA-256 of the sanitized diagnostic message. Line and column are deliberately excluded so harmless source movement does not invalidate a reviewed signature. All diagnostic signatures in the result must match exactly; subset matches are rejected. Duplicate entry IDs, duplicate match definitions, unknown fields, unsorted signatures and non-finite or duplicate-key JSON fail closed.

The registry stores hashes of sanitized messages, not raw logs or fixes. A registry entry is not a memory record and does not prove a root cause. Project-specific entries remain owned by the project; a reusable entry belongs here only when the cause is shared infrastructure or confirmed across at least two projects.

## Classification

| Condition | Classification | Route |
|---|---|---|
| Result is not `FAIL` | `not_applicable` | `none` |
| `FAIL` has no exact entry | `unmatched` | `agent` |
| Exact entry is before `created_at` | `inactive_match` | `agent` |
| Exact entry reached `expires_at` | `expired_match` | `agent` |
| Exact entry is within its validity window | `known_failure` | `machine` |

Every classification sets `automatic_retry_allowed=false`. `route=machine` means deterministic handling may be proposed; it is not execution authority. A later retry needs a new Policy Gate decision bound to that attempt and budget.

`--as-of` is a required explicit UTC timestamp. This keeps classification deterministic and makes expiry evidence reproducible instead of silently reading the local clock.

## Output and identity

`bima-known-failure-classification.v1` records:

- classification and route;
- the constant retry denial;
- canonical semantic SHA-256 of the parsed result and registry;
- result verdict and equivalence key;
- explicit `as_of` time;
- matched entry ID, owner, reviewer, validity window and evidence reference when applicable.

The classifier does not mutate `bima-verification-result.v2`, so the native failed attempt remains intact.

## CLI

```text
python -I automation/known_failure_registry.py \
  --result <bima-verification-result.v2.json> \
  --registry <bima-known-failure-registry.v1.json> \
  --as-of 2026-09-15T00:00:00Z \
  --output <trusted-output-directory>
```

The CLI writes `classification.json`; exit code `0` means classification completed, including unmatched/expired states. Contract, input or filesystem errors return `2`. Consumers must inspect `classification`, not interpret CLI success as a verification pass.
