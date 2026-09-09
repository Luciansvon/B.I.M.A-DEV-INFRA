# GitHub automation security contract

## Identity

Name: offline zizmor gate. Stability: **experimental**. Purpose: detect security mistakes in GitHub workflows, local Actions, and Dependabot configuration before hosted CI or agent escalation.

## Scope and command

Zizmor v1.30.0 runs with its default regular persona through prek:

```text
zizmor --offline --strict-collection --no-progress --color=never --render-links=never --show-audit-urls=always <selected files>
```

The mode is read-only: no `--fix`, remote repository input, GitHub token, API request, or Docker runtime. Strict collection makes malformed selected inputs fail instead of being skipped. Prek selects workflow definitions, local Action definitions, and `.github/dependabot.yml` when those files are checked.

## GitHub adapter and evidence

The existing Ubuntu workflow-lint job downloads the v1.30.0 Linux amd64 archive, verifies SHA-256 `ec8c95cd800845abb9bbc5f377ec7c57d2eb8e2386a00a201d3a74ee4092e5ed`, and runs `task preflight`. The retained `.artifacts/prek.log` records the zizmor version and hook result. No separate job, permission, secret, or publish side effect is added.

## Failure contract

Any emitted finding or strict collection error fails pre-flight and CI. Findings must be fixed or narrowly suppressed with a reviewed explanation; a green exit without the retained hook evidence is insufficient. Dependabot routine version updates use a seven-day cooldown, while security updates remain immediate under GitHub's cooldown semantics.

## Boundaries

`--offline` disables audits that require GitHub metadata. A pass therefore does not prove Action commit provenance, detect every stale or archived dependency, inspect repository settings, scan application dependencies, or replace GitHub security features. The default regular persona prioritizes lower false-positive risk; auditor/pedantic findings are outside this initial gate.

## Compatibility

Official v1.30.0 standalone archives cover Linux, Windows, and macOS. Tool, persona, selected inputs, or audit-mode changes require local positive/negative evidence, checksum review, and hosted validation.
