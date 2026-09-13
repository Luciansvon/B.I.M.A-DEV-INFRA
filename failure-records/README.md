# Reviewed failure records

`records.json` is the portable, reviewed source set for future failure retrieval. It currently contains five real, active shared-infrastructure records with reproduced evidence, a confirmed cause, a scoped fix, relevant re-verification, a record owner and independent review.

Synthetic unit-test fixtures never count toward the 100-real-case retrieval gate. Project records remain in their owning project; only a shared-infrastructure cause or the same confirmed root cause in at least two projects can be promoted here.

The production activation gate remains blocked at `5/100` real records and `0/10` held-out queries. Live SQLite/FTS files must remain outside this repository and outside OneDrive or another synchronized/network directory.
