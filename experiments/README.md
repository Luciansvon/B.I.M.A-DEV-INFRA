# Gated experiments

No optional provider experiment is active. `automation/experiment_gate.py` requires reviewed demand from at least two distinct projects, a pinned dataset and baseline evidence, predeclared acceptance thresholds, bounded resources, reject criteria and rollback before it can return `READY`.

`READY` is not execution authorization. Policy Gate approval is still required, and the experiment gate never starts a provider, model, sandbox or external service. Local-QA SLM requests additionally require at least 1,000 verified benchmark cases with a held-out split.
