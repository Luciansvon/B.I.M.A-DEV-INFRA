# Failure-memory benchmark v1

Status: **Executable mechanics; production benchmark blocked at 5/100 records and 0/10 held-out queries.**

The benchmark request binds a held-out query set to the canonical failure-record digest and declares acceptance thresholds before execution. At least 100 real, reviewed, `ACTIVE` failure records and 10 held-out queries are required before the SQLite index is built.

Metrics use deterministic integer parts-per-million:

- recall at the declared `k`;
- mean reciprocal rank;
- false-match rate among returned records;
- stale/forbidden-hit rate.

Every query declares its project access scope, relevant active record IDs and forbidden record IDs. Dataset/digest mismatches, unknown references, duplicate keys, non-finite values and relevant/forbidden overlap fail closed. A benchmark miss returns `FAIL`; missing prerequisites return `BLOCKED`; neither becomes `PASS`.

```text
python -I automation/failure_memory_benchmark.py \
  --records failure-records/records.json \
  --queries benchmarks/failure-memory/held-out.json \
  --database <local-nonsynced-path>/failure-memory-benchmark.sqlite3 \
  --repository-root . \
  --report .artifacts/failure-memory-benchmark/report.json
```

The checked-in production query set remains empty until the corpus is large enough to freeze at least 10 genuinely held-out queries. Synthetic unit cases prove metric calculation and gate behavior only.
