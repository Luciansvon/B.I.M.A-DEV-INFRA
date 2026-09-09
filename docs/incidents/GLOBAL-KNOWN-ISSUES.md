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

## GKI-0001 — Text checkout conversion changes evidence byte hashes

Status: Open
First observed: 2026-09-08
Last verified: 2026-09-09
Affected layer: integration / evidence
Affected projects:

- `Luciansvon/B.I.M.A-DEV-INFRA`
- `Luciansvon/AI-COLOR-COMPARE`

### Symptom

The same committed text policy or validator can produce a different SHA-256 in a Windows working tree and a GitHub-hosted Linux checkout. Semantic content appears identical, but canonical evidence differs because the contract hashes exact bytes.

### Root cause

Git text checkout conversion changes LF bytes to CRLF when `core.autocrlf=true` and the consuming repository has no explicit end-of-line attribute for evidence inputs. B.I.M.A-DEV-INFRA previously observed this on its validator and policy before adding `.gitattributes`. AI-COLOR-COMPARE reproduced it for `bima-audit-policy.json`: the committed blob and hosted evidence hash are `c5e5b99cf78377356497c49cd3fb6217f81fd263cde1bd677ede58b5b11a436f`, while the Windows checkout hash is `fdf9e656a5f935c9d56b13fa28f8f1ffdfe589729b72509b8434925d038819f5`.

### Detection

Compare the committed blob SHA-256, the local working-file SHA-256, and `policy_sha256` or `validator_sha256` in hosted evidence. Check `git check-attr text eol -- <path>` and `core.autocrlf` before attributing the difference to tool behavior.

### Fix

Add a project-owned `.gitattributes` rule that pins shared policy and evidence-input text files to LF, then renormalize through review and regenerate evidence. Do not rewrite unrelated source files merely to fix one contract input.

### Prevention

The project-integration guide should require explicit EOL rules for byte-hashed text inputs. Consumer validation should compare committed bytes with hosted evidence and label dirty/local hashes separately.

### Evidence

- [Initial DEV-INFRA validation](../audits/VALIDATION-2026-09-08.md)
- [AI-COLOR-COMPARE consumer validation](../audits/VALIDATION-2026-09-09-AI-COLOR-CONSUMER.md)
- [AI-COLOR-COMPARE pin-update PR](https://github.com/Luciansvon/AI-COLOR-COMPARE/pull/13)
