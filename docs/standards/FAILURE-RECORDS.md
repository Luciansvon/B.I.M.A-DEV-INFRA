# Portable failure records v1

Status: **Executable contract; production corpus has 5/100 active real records.**

`bima-failure-record-set.v1` is the portable source of truth. Each record contains reproduced failure evidence, confirmed cause evidence, scoped fix and verification evidence, owner, independent reviewer, lifecycle, access policy and supersession links. Strict JSON parsing rejects duplicate keys, non-finite values, unknown fields, invalid ordering and inconsistent lifecycle links.

Records are either `real` or `synthetic`. Synthetic fixtures prove mechanics but never count toward activation. Only `real` records with `ACTIVE` lifecycle count toward `real_verified_records`; invalidated, expired, superseded or revalidation-required history cannot satisfy the corpus gate. A global record is allowed only when the cause belongs to shared infrastructure or the same confirmed root cause is evidenced in at least two repositories. Similar symptoms are insufficient.

Lifecycle values are `ACTIVE`, `SUPERSEDED`, `EXPIRED`, `INVALIDATED` and `REVALIDATION_REQUIRED`. Historical records are retained for audit, but only active records are eligible for retrieval. Restricted records require an explicit project allowlist.

```text
python -I automation/failure_records.py --input failure-records/records.json --output .artifacts/failure-records
```

The command emits canonical `records.json` and `summary.json`. Exit `0` means the contract is valid, not that enough real cases exist.
