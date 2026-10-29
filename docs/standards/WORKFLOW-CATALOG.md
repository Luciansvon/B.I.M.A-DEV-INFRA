# Reusable workflow catalog

Status: **experimental**. A reviewed index, not a registry service or a pinning authority.

## Identity

`catalog/workflows.json` lists the reusable workflows this repository publishes. `automation/workflow_catalog.py` validates the catalog against the workflow files and their documentation.

## Entry contract

Every entry has exactly these fields:

| Field | Meaning |
|---|---|
| `id` | Lowercase kebab-case identifier, at most 40 characters, unique |
| `path` | `.github/workflows/<name>.yml`; must exist and declare `workflow_call:` |
| `status` | `experimental`, `beta` or `stable` |
| `docs` | `docs/standards/<NAME>.md`; must exist |
| `consumers` | Zero or more `owner/repository` strings, unique |
| `sha256` | SHA-256 of the workflow file |
| `summary` | One printable line, at most 200 characters |

The top level has exactly `schema` (constant `bima-workflow-catalog.v1`), `schema_version` (integer `1`) and `workflows` (1–50 entries). Unknown fields, duplicate keys, non-finite numbers and duplicate IDs fail closed.

## Validation

```bash
python -I automation/workflow_catalog.py
# or
task catalog
```

The check fails when a listed workflow or documentation file is missing, a workflow does not declare `workflow_call:`, a declared input or output is not named in its documentation, a required contract section is missing or empty, the recorded SHA-256 does not match the file, or the entry shape is wrong. Output: `workflow-catalog: pass; workflows=<n>`.

The document shape is published as `schemas/bima-workflow-catalog.v1.schema.json` and its field sets are checked against `automation/workflow_catalog.py` by `tests/test_schema_contract_parity.py`.

The SHA-256 pins the reviewed workflow bytes. Any workflow edit requires a catalog update in the same change; that is intentional review friction, not an automation failure.

## Adding or changing a workflow

1. Add or edit the reusable workflow and its `docs/standards/` document.
2. Add or update the catalog entry, including the new SHA-256.
3. Run the validator and the regression tests.
4. Record consumer adoption separately; the catalog `consumers` list reflects proven callers, not intentions.

## Boundaries

The catalog does not resolve or update consumer pins, prove that a consumer ran the workflow, sign entries, or replace the workflow's own contract document. It checks structure, file existence and byte identity only.
