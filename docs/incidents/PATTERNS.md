# Incident Patterns

## Routing model

```text
FAILURE
  |
  v
PROJECT ISSUE / INCIDENT
  |
  v
REPRODUCE + COLLECT EVIDENCE
  |
  v
ROOT CAUSE CONFIRMED?
  |\
  | no -> keep investigating
  |
  yes
  |
  +--> project-specific -> fix + close locally
  |
  +--> shared infra / same root cause >=2 projects
             |
             v
      GLOBAL KNOWN ISSUE
             |
             v
 shared prevention / workflow / rule update
```

## Never promote by symptom alone

These can look identical while having different causes:

- timeout
- blank screen
- missing artifact
- dependency install failure
- out-of-memory
- permissions denied

Promotion requires root-cause equivalence.

## Evidence checklist

Before promoting an incident, collect as many as applicable:

- affected repository + issue/PR
- workflow run / job
- runner OS and labels
- relevant tool versions
- exact failure step
- minimal reproduction
- logs
- before/after result
- fix commit/PR

## Relationship to ADRs

If an incident causes a lasting architecture or policy change, create an ADR and link it from the known issue.

Example:

```text
GKI-001 persistent runner contamination
        |
        +--> fix runner cleanup
        |
        +--> ADR: prefer ephemeral runner for untrusted workloads
```
