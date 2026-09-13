# Failure memory v1

Status: **Index mechanics verified; production activation blocked at 5/100 real cases.**

The portable record set is authoritative. SQLite with FTS5 is a disposable, single-writer derived index. A build requires at least 100 real, reviewed, `ACTIVE` records; below that threshold the command returns `BLOCKED`, exit `3`, and creates no database.

Databases and backups must remain outside the repository, OneDrive or another synchronized folder, and network paths. Build uses a fresh `.building` target, verifies SQLite integrity and FTS5 support, records the canonical source digest, then atomically publishes the new database. Existing targets are never overwritten.

Only `ACTIVE` records are indexed. Export reconstructs and digest-checks the complete portable source set. Search applies access filtering after lexical matching. Backups use the SQLite backup API and integrity checking.

```text
python -I automation/failure_memory.py \
  --input failure-records/records.json \
  --database <local-nonsynced-path>/failure-memory.sqlite3 \
  --repository-root . \
  --report .artifacts/failure-memory/report.json
```

Unit tests use exactly 100 synthetic records to prove build, BM25 search, invalidation exclusion, access filtering, export round-trip, backup and rebuild. Those fixtures do not satisfy the production gate.

Retrieval adoption additionally requires the [held-out benchmark gate](FAILURE-MEMORY-BENCHMARK.md). A buildable index alone does not prove useful retrieval quality.
