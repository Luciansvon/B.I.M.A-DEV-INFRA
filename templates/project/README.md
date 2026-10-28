# __PROJECT_NAME__

Describe what this project does, who uses it and what it does not cover.

## Build and test

```bash
# Fill in the real commands before the first merge.
```

## Shared infrastructure

This repository calls the B.I.M.A-DEV-INFRA repository audit, pinned to `__INFRA_REF__`:

- policy: `.bima/audit.json`
- workflow: `.github/workflows/bima-shared-audit.yml`

Keep the workflow reference and the `infra-ref` input at the same reviewed commit; update both together.

## Architecture and incidents

- [Architecture](ARCHITECTURE.md)
- [Incidents](INCIDENTS.md)
