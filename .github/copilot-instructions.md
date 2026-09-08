# Repository Instructions

Before making changes, read:

- `AGENTS.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/PROJECT-CONTRACT.md`
- relevant `docs/decisions/`
- relevant `docs/incidents/`

Rules:

1. Keep this repository project-agnostic.
2. Shared infrastructure and cross-project knowledge belong here; app-specific architecture/incidents belong in the app repository.
3. Promote an incident globally only after matching root cause is confirmed in >=2 projects, or the cause belongs to shared infrastructure.
4. Reusable workflows must follow `docs/standards/WORKFLOW-CONTRACT.md`.
5. Prefer reusable capabilities over copied YAML or project-name conditionals.
6. Use least privilege, explicit timeouts, reproducible versions, and inspectable evidence.
7. Never commit secrets, production databases, large model weights, or unrelated binary archives.
8. Record durable shared architecture/policy changes as ADRs.
9. Preserve research evidence and source ledgers.
10. Do not claim validation passed when tests/evidence are missing or blocked.
