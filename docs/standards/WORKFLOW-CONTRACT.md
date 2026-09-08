# Reusable Workflow Contract

Every reusable workflow added to B.I.M.A-DEV-INFRA must document the following.

## Required contract

### Identity

- Name
- Purpose
- Stability: experimental | beta | stable

### Triggers

Supported events and whether manual/API invocation is allowed.

### Inputs

| Input | Required | Type | Default | Description |
|---|---:|---|---|---|
| | | | | |

### Outputs

| Output | Type | Description |
|---|---|---|
| | | |

### Runner

- GitHub-hosted or self-hosted
- OS/architecture
- required labels
- hardware/device requirements

### Permissions

List the minimum `GITHUB_TOKEN` permissions and any external credentials/OIDC requirements.

### Execution limits

- timeout
- concurrency policy
- retry policy
- expected runtime class

### Evidence

Workflow must produce at least one inspectable result:

- check/status
- report
- artifact
- structured JSON
- benchmark result
- release/provenance

### Failure contract

Define what makes the workflow fail vs warn vs skip.

### Security

Document:

- untrusted input handling
- third-party actions/dependencies
- pinning strategy
- secret exposure risks
- self-hosted runner trust boundary

### Compatibility

Document breaking changes and migration requirements.

## Design rules

- Do not branch behavior by hard-coded project name unless the capability is genuinely project-specific and belongs outside shared infra.
- Prefer explicit inputs over hidden repository assumptions.
- Prefer reusable modules over copied YAML.
- Shared workflow results should be machine-readable where practical.
- A successful exit code without evidence is not sufficient for critical workflows.
