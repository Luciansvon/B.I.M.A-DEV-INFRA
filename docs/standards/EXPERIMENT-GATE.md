# Experiment readiness gate v1

Status: **Executable gate; no experiment/provider active.**

Every request declares a capability, pinned baseline and dataset evidence, acceptance thresholds, budget, permissions, reject criteria, rollback and independently reviewed demand. `READY` requires the same unmet capability in at least two distinct project repositories. Local QA SLM requests additionally require at least 1,000 verified cases and a held-out dataset.

The decision is deterministic and records the request digest, distinct demand count, reason and unmet requirements. `BLOCKED` exits `3`; malformed input exits `2`. `READY` exits `0` but still records `requires_policy_authorization=true` and `execution_started=false`.

```text
python -I automation/experiment_gate.py --request <request.json> --output .artifacts/experiment-gate
```

The gate never installs or starts a provider, model, database, sandbox, durable workflow, graph service or security-response system. Readiness and execution authority are separate controls.
