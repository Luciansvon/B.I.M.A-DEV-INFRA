# Failure-memory benchmark

The production request is intentionally empty while the reviewed record corpus is `0/100`. The benchmark therefore returns `BLOCKED` and creates no SQLite database.

Queries must be held out from indexed record text and declare relevant plus forbidden record IDs. Results use deterministic integer parts-per-million for recall at k, mean reciprocal rank, false matches and stale/forbidden hits. Populate this ledger only from reviewed real cases; synthetic unit fixtures never count as production evidence.
