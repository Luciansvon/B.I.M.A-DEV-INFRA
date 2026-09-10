# Known failure registry v1 local validation

Date: 2026-09-10

Scope: deterministic exact-match classification for one bounded, synthetic same-attempt diagnostic fixture.

Status: **LOCAL AND HOSTED REGRESSION PASS; CONSUMER INTEGRATION PENDING.**

## Evidence

Focused command:

```text
python -I -m unittest discover -s tests -p test_known_failure_registry.py -v
```

Result: 11 passed, 0 failed.

Full regression command:

```text
python -I -m unittest discover -s tests -v
```

Result: 72 passed, 1 skipped, 0 failed. The local Windows account cannot create the symlink required by the skipped repository-audit test; hosted Windows previously exercised that test successfully.

Repository audit: 100 files, 146 supported local links, zero findings. Canonical v1 audit evidence remained `pass`, SHA-256 `9986777d59354919e052f3a701de7c14c2648722880a8d9d831137e27d29afd7`; the implementation tree was correctly marked dirty at revision `42110d114feff66d53b0f95648bd087bc6992584`.

Hosted post-merge Infrastructure CI run [`34446812166`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34446812166) verified revision `d342504f294e5ea902f36a06128ebf952abbc039`:

- Ubuntu 24.04: 72 tests passed; repository audit passed with 100 files, 146 local links and zero findings;
- Windows 2025: 72 tests passed, including the symlink rejection test unavailable to the local account; repository audit passed with the same counts and zero findings;
- canonical audit evidence matched byte-for-byte across both systems, SHA-256 `9696a5bb5234042227f85281db6ffacf68d13ccc6b9ee72a2a889208c80dd8f3`;
- both PASS artifacts contained zero agent packet files;
- workflow lint, prek, action-validator, pinact and zizmor passed.

Covered behavior:

- an active exact owner-reviewed entry routes to `machine` while preserving `automatic_retry_allowed=false`;
- an expired or not-yet-created exact entry routes to `agent`;
- changed message, environment or diagnostic cardinality does not match;
- non-FAIL results are not applicable;
- owner, reviewer and expiry are mandatory, with a maximum 90-day validity;
- duplicate match definitions and unsorted/duplicate signatures fail closed;
- duplicate-key, non-finite and unknown-field JSON fail closed;
- internally inconsistent result counts or FAIL/exit combinations fail closed;
- classification bytes and semantic input digests are deterministic;
- the isolated CLI writes bounded classification evidence.

## Evidence boundary

The checked-in entry is synthetic and proves only the registry contract. It is deliberately not assembled from the historical AI-COLOR-COMPARE TypeScript and Rust runs because those runs have different revisions and command identities. Hosted cross-platform regression is proven for DEV-INFRA itself. No retry, repair, model call, workflow integration or consumer pin change is included; a project-owned live registry decision remains pending.
