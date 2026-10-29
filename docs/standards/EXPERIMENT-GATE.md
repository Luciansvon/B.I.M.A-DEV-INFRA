# Experiment readiness gate v1

Status: **Executable gate; no experiment/provider active.**

Every request declares a capability, pinned baseline and dataset evidence, acceptance thresholds, budget, permissions, reject criteria, rollback and independently reviewed demand. `READY` requires the same unmet capability in at least two distinct project repositories. Local QA SLM requests additionally require at least 1,000 verified cases and a held-out dataset.

## Demand identity

Each `demand_evidence` record has exactly `project_id`, `repository`, `capability`, `requirement_ref` and `reviewed_by`.

- `capability` must equal the request-level `capability` and one of the `CAPABILITIES` identifiers. Unknown capabilities and mixed-capability demand fail closed; two projects asking for different capabilities do not satisfy the gate.
- `requirement_ref` must be `owner/repo#number` or an `https://` URL. Empty, `TBD` and other placeholders fail closed.
- `reviewed_by` must be a non-empty reviewer identity, not a placeholder.
- Records must be sorted, name one distinct project and one distinct repository each, and must not repeat the same `repository` + `requirement_ref` pair.

Demand is evidence of an unmet need, not execution permission. The gate never authorizes, loads or starts a provider, model, database, sandbox, durable workflow, graph service or security-response system.

## Decision

The decision is deterministic and records the request digest, distinct demand count, reason and unmet requirements. `BLOCKED` exits `3`; malformed input exits `2`. `READY` exits `0` but still records `requires_policy_authorization=true` and `execution_started=false`.

```text
python -I automation/experiment_gate.py --request <request.json> --output .artifacts/experiment-gate
```

## Compatibility

The v1 demand record now requires `capability`. This is a fail-closed tightening made before any provider or consumer adoption: requests written before the change fail validation and must be regenerated with a capability. No accepted request bytes or decision meanings change. A future change to field meaning requires a new schema version and an ADR.
