# Repository governance validation

Date: 2026-09-12; license decision refreshed 2026-09-13

Status: **LOCAL GOVERNANCE PASS; HOSTED LICENSE DETECTION PENDING.**

Live GitHub REST state for `Luciansvon/B.I.M.A-DEV-INFRA` reported:

- Actions enabled;
- allowed actions: `all`;
- repository-level `sha_pinning_required=true`;
- no repository rulesets; classic branch protection remains authoritative;
- required checks are `Workflow lint`, `Repository audit (ubuntu-24.04)` and `Repository audit (windows-2025)`;
- strict required-check updates, admin enforcement, linear history and conversation resolution enabled;
- force-push and branch deletion disabled;
- solo-maintainer approval count `0`.

Pinact 4.1.1 reports no mutable external Action references in the current worktree. Local actions remain repository-relative and are reviewed with their caller revision. Actionlint and zizmor also report zero findings for the P0-P5 branch.

The selected-actions endpoint returns HTTP 409 because `allowed_actions=all`; this does not disable SHA enforcement. SHA enforcement constrains Action references but does not prove Action behavior, workflow correctness or artifact provenance. Those remain separate checks.

The owner authorized completion of the license decision on 2026-09-13. Apache-2.0 was selected for permissive cross-project reuse, its explicit contributor patent grant and its change-notice obligations. The canonical `LICENSE` file is byte-equal to GitHub's license template after ignoring the terminal newline; GitHub license detection remains to be verified after publication.
