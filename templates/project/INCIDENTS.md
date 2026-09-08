# Project Incidents Template

> Copy this into the consuming project repository, or use equivalent GitHub Issues. Project-specific incidents stay with the project unless promoted by the global criteria.

## Incident format

```md
## INC-0001 — Short title

Status: Open | Investigating | Mitigated | Resolved
First observed: YYYY-MM-DD
Affected version/commit:
Environment:
Related issue/PR:

### Symptom
What happened.

### Reproduction
Minimal reproducible steps.

### Evidence
Logs, screenshots, workflow runs, metrics, artifacts.

### Root cause
Confirmed cause. Do not guess.

### Fix
Corrective change.

### Validation
How the fix was proven.

### Recurrence risk
What could make it happen again.

### Global promotion check
- [ ] Same root cause seen in another project
- [ ] Root cause belongs to shared infrastructure
- [ ] Shared prevention/change required

If any box is confirmed, link/create an entry in `B.I.M.A-DEV-INFRA/docs/incidents/GLOBAL-KNOWN-ISSUES.md`.
```

---

_No project incidents recorded in this template._
