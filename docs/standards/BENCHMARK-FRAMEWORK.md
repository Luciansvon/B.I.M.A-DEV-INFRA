# Benchmark framework v1

Status: **Shared contract mechanics and one executable adapter; no generic runner.**

A benchmark is a gated comparison against a frozen baseline. It is not a test suite and not a dashboard. Each adapter declares, before execution:

- a stable `benchmark_id` and a dataset or task digest;
- the baseline identity and the environment that produced it;
- deterministic acceptance thresholds;
- bounded inputs and sample counts;
- the evidence it will retain.

## Shared mechanics

`automation/benchmark_contract.py` holds the dependency-free mechanics reviewed for every adapter: strict UTF-8 JSON, canonical bytes and digests, identifier/SHA-256/parts-per-million validation, bounded sorted IDs and bounded input loading. Adapters keep their domain metrics; they do not reimplement these checks.

Results use `PASS`, `FAIL`, `BLOCKED` or `UNKNOWN`. Missing data, missing prerequisites or an unbound dataset never becomes `PASS`. `BLOCKED` is a valid outcome and stays visible in the verification aggregate.

## Adapters

`automation/failure_memory_benchmark.py` is the first adapter. It binds the held-out query set to the canonical record digest and gates on corpus size, held-out status and query count before building the index.

An adapter owns its:

- request and report schema;
- dataset binding and validation;
- metric calculation, in deterministic integer units;
- acceptance evaluation;
- retained query or sample details.

The adapter must fail closed on unknown references, duplicate keys, non-finite values, stale digests and malformed thresholds.

## Adding an adapter

1. Name a real consumer and the decision the benchmark supports.
2. Freeze the dataset or task identity and the baseline before the first run.
3. Write acceptance thresholds down in the request, not after seeing results.
4. Reuse `benchmark_contract` for parsing, bounds and canonical evidence.
5. Retain the report and the exact command or workflow that produced it.
6. Prove the `BLOCKED` path as well as the `PASS` and `FAIL` paths.

## Not in scope

No generic runner, scheduler, hosted benchmark service, benchmark database or dashboard. Those are added only when a second real benchmark needs the same execution surface, not because the contract exists.
