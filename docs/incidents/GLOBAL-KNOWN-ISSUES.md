# Global Known Issues

This file stores **cross-project or shared-infrastructure failure patterns**, not every project bug.

## Promotion criteria

Add an entry only when at least one is true:

- the same confirmed root cause affects 2 or more projects;
- the root cause is in B.I.M.A-DEV-INFRA shared workflow/runner/security infrastructure;
- prevention requires changing a shared rule, workflow, runner image, contract, or reusable action.

Do not promote based only on similar symptoms.

## Entry format

```md
## GKI-0001 — Short title

Status: Open | Mitigated | Resolved
First observed: YYYY-MM-DD
Last verified: YYYY-MM-DD
Affected layer: workflow | runner | dependency | security | artifact | integration | other
Affected projects:
- owner/repo#issue

### Symptom
What users/workflows observe.

### Root cause
Confirmed technical cause.

### Detection
How to detect or reproduce it reliably.

### Fix
Known corrective action.

### Prevention
Shared change that prevents recurrence.

### Evidence
Logs, commits, PRs, reports, or external references.
```

---

_No promoted global incidents yet._
