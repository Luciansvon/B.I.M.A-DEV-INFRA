# Shared workflow security baseline

Status: initial baseline; repository settings are a separate enforcement layer.

## Executable baseline

- Declare `permissions: contents: read`; add write scopes only for a documented module that needs them.
- Pin external Actions and consumed infrastructure to full commit SHAs. Dependabot proposes Actions updates; humans review them and their check results.
- Verify downloaded CI tools against a fixed SHA-256 digest before execution. The current `actionlint`, prek, action-validator, pinact, and zizmor release binaries are versioned and digest-checked.
- Enforce full-length commit SHAs for remote Actions and reusable workflows with pinact's read-only offline mode. This baseline does not yet verify version comments, SHA provenance, or minimum release age.
- Run zizmor's regular-persona offline audits without automatic fixes. The gate covers locally decidable GitHub workflow, local Action, and Dependabot risks; online-only audits remain explicitly outside this increment.
- Delay routine Dependabot version updates for seven days. GitHub security updates are not delayed by this cooldown.
- Use GitHub-hosted ephemeral runners for untrusted pull requests. No `pull_request_target` execution of PR code, self-hosted runner, deployment environment, or inherited secrets in the initial audit module.
- Disable persisted checkout credentials. Pass configurable strings through environment variables or action inputs; never interpolate them into shell source.
- Keep caller checkout (`subject`) separate from executable infrastructure (`infra`). The shared audit never executes caller scripts, installs caller dependencies, or imports caller Python modules. Python runs with `-I`.
- Set explicit job timeouts. Upload the named evidence files even after a check fails, and fail when evidence is missing. Never upload a whole checkout or arbitrary caller-selected artifact path.
- Retain artifacts for 14 days. Reports contain repository file paths and finding metadata, not file content; consumers must consider whether their filenames are sensitive.

## Repository settings still required

After hosted checks have actually run, configure a `main` ruleset requiring pull requests and both `Repository audit (ubuntu-24.04)` and `Repository audit (windows-2025)` checks. Prevent force pushes and branch deletion. The owner must choose review-count and administrator-bypass policies appropriate for a solo-maintained repository.

The audit on 2026-09-08 found no branch protection or rulesets. Adding YAML alone does not prevent bypassing a failing check. Repository administration settings were inspected, not modified.

The token default was already read-only and workflow PR approval was disabled. Repository-level SHA pinning was not required, and all Actions were allowed. The shipped workflow pins are narrower than those repository settings.

## What this does not prove

Repository hygiene and offline workflow checks do not provide platform-side repository analysis, discover vulnerable application dependencies, analyze application source, validate every workflow security property, or establish release readiness. Keep those gates explicit when their modules are added. A policy or ignore change can weaken a check; review it together with workflow and validator changes.

## Runner and version policy

The initial reusable workflow supports `ubuntu-24.04` GitHub-hosted runners. Infrastructure tests also target `windows-2025`. Neither OS label makes the rolling hosted image immutable. Python is pinned to `3.13.15`, matching local validation and an available `actions/python-versions` release; refresh it deliberately with regression evidence. Action pins were resolved against upstream GitHub refs on 2026-09-08. Repository text policies force LF for stable validator and policy byte hashes across hosted operating systems.

Self-hosted, GPU, ARM, macOS, private network, and hardware workflows need their own documented trust boundary before activation.

Sources: [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use), [reusing workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows).
