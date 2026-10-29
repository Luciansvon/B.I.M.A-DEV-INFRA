# Portable failure records v1

Status: **Executable contract; production corpus remains below the 100-record activation threshold.**

`bima-failure-record-set.v1` is the portable source of truth. Each record contains reproduced failure evidence, confirmed cause evidence, scoped fix and verification evidence, owner, independent reviewer, lifecycle, access policy and supersession links. Strict JSON parsing rejects duplicate keys, non-finite values, unknown fields, invalid ordering and inconsistent lifecycle links.

Records are either `real` or `synthetic`. Synthetic fixtures prove mechanics but never count toward activation. Only `real` records with `ACTIVE` lifecycle count toward `real_verified_records`; invalidated, expired, superseded or revalidation-required history cannot satisfy the corpus gate. A global record is allowed only when the cause belongs to shared infrastructure or the same confirmed root cause is evidenced in at least two repositories. Similar symptoms are insufficient.

Review is executable, not declarative. The reviewer must differ from the owner case-insensitively, the review timestamp must follow cause confirmation, a record cannot expire before its last revalidation, and two records with the same case kind, signature and repository set are rejected as duplicates. Evidence references must be absolute URIs, and `real` records must use `https` references, so fixture-scheme evidence cannot masquerade as a real case. `summarize()` validates the whole set before counting, so a record that fails any of these checks cannot contribute to `real_verified_records`.

Lifecycle values are `ACTIVE`, `SUPERSEDED`, `EXPIRED`, `INVALIDATED` and `REVALIDATION_REQUIRED`. Historical records are retained for audit, but only active records are eligible for retrieval. Restricted records require an explicit project allowlist.

```text
python -I automation/failure_records.py --input failure-records/records.json --output .artifacts/failure-records
```

The command emits canonical `records.json` and `summary.json`. Exit `0` means the contract is valid, not that enough real cases exist.
