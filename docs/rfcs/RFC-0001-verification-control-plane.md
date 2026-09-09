# RFC-0001 — Evidence-first verification control plane

Status: **Proposed**

Date: 2026-09-09

Owners: B.I.M.A-DEV-INFRA maintainers

Related issues: [#3](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/3), [#8](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/8), [#9](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/issues/9)

## Summary

This RFC proposes evolving B.I.M.A-DEV-INFRA into a project-agnostic verification control plane. Projects provide explicit configuration and project-owned commands. Shared infrastructure coordinates deterministic verification, normalizes evidence, applies reviewed policy, and escalates only unresolved failures.

The proposal does **not** authorize a universal scanner bundle, automatic fixes, a local model runtime, a repository restructure, or a fleet dashboard. Each capability must earn adoption through a real consumer, bounded implementation, retained evidence, and measured value.

## Decision requested

Reviewers are asked to decide whether to:

1. adopt the control-plane direction and responsibility boundaries;
2. use ReleaseProof Core as the first new consumer-driven module;
3. keep project discovery advisory and project configuration authoritative;
4. keep deterministic rules and failure memory ahead of any local language model; and
5. require a focused ADR and current validation for each implemented phase.

Accepting this RFC approves a direction, not every candidate tool.

## Context

The current repository has an experimental deterministic path:

```text
Task command
    |
repository audit
    |
bima-evidence.v1
    |
bima-agent-packet.v1 on non-pass only
```

Hosted Ubuntu and Windows validation exists for that path. A published consumer reference, repository protection, an explicit repository license, and a real project integration are still pending. Repository hygiene evidence is not application, security, artifact, or release readiness.

Issue #8 proposes ReleaseProof for source-to-release verification. Issue #9 proposes an optional local model for bounded failure triage. This RFC places both inside one machine-first architecture without making either a mandatory dependency of every project.

## Goals

- Reduce repeated agent work on deterministic checks.
- Give local execution, CI, humans, and agents the same command and evidence contracts.
- Keep application-specific knowledge in the owning project.
- Build and verify the same artifact where release semantics require it.
- Preserve inspectable evidence for pass, warning, failure, error, and skip outcomes.
- Make unknown states explicit and safe to escalate.
- Measure time, compute, maintenance, and agent work saved.

## Non-goals

- Building a new CI platform.
- Running every analyzer against every repository.
- Replacing native test runners, package managers, or mature security tools.
- Inferring an application's architecture without project confirmation.
- Treating SARIF as the format for every result type.
- Automatically changing `FAIL` to `PASS` through an agent or model.
- Running untrusted pull requests on a privileged persistent runner.
- Storing model weights, raw private logs, or large release binaries in Git.

## Proposed architecture

```text
PROJECT / HUMAN / API / SCHEDULE
                 |
          project contract
                 |
        advisory discovery
                 |
        execution tier/router
                 |
     shared module + project adapter
                 |
       native result and evidence
                 |
          canonical envelope
                 |
         deterministic policy
        /          |          \
      PASS     KNOWN FAIL    UNKNOWN
        |           |           |
      done     machine rule   bounded packet
                                |
                         failure retrieval
                                |
                     optional local model
                                |
                     abstain/escalation gate
                                |
                           strong agent
                                |
                    reviewed patch or advice
                                |
                    deterministic verification
```

An agent may propose a change only when authorized by the calling workflow or human. It does not approve its own result, bypass a failed gate, publish a release, or write directly to a protected branch.

## Responsibility boundary

### Project repository owns

- application architecture and project ADRs;
- build, lint, test, benchmark, package, and smoke-test commands;
- expected artifact paths and release strategy;
- project-specific thresholds, exceptions, and incidents;
- device, service, credential, and platform requirements.

### B.I.M.A-DEV-INFRA owns

- reusable orchestration and adapter contracts;
- shared evidence schemas and status semantics;
- shared security and runner policies;
- cross-project failure patterns with confirmed common root causes;
- generic reporters, normalization, and policy evaluation;
- compatibility and migration documentation.

## Project profile and discovery

The first new contract should be a versioned project profile, for example `.bima/project.yml`. The exact schema requires a separate ADR and regression fixtures.

```yaml
schema: bima-project.v1
project:
  type: windows-desktop
  platforms: [windows]
commands:
  test: task test
  package: task package
artifacts:
  - id: windows-installer
    path: dist/*.exe
capabilities:
  releaseproof: required
  native_binary_analysis: optional
```

Discovery may inspect manifests, lockfiles, source extensions, and build metadata to propose a profile. It must:

- label every inferred value as detected rather than declared;
- never override an explicit project value silently;
- never execute commands merely because they appear in an untrusted branch;
- emit a report that shows declared, detected, conflicting, and unknown fields.

Tree-sitter and ast-grep remain optional source adapters. A syntax tree alone is not an authoritative dependency graph or affected-test selector. Native build-system impact analysis should be preferred when available.

## Evidence model

`bima-evidence` remains the shared semantic envelope. Module-native formats remain intact and are referenced rather than flattened into one lossy format.

| Evidence type | Preferred native representation |
|---|---|
| Static-analysis findings | SARIF where supported |
| Tests | JUnit or runner-native structured output |
| SBOM | SPDX or CycloneDX |
| Provenance | in-toto/SLSA-compatible attestation |
| Benchmark | Versioned benchmark schema |
| Release verification | Versioned ReleaseProof result |
| Agent routing | `bima-agent-packet.v1` |

Canonical evidence contains stable semantic fields. Execution metadata contains timestamps, runner details, raw-input hashes, and other volatile values. A canonical match proves only the recorded fields.

## Policy

Tools produce facts. Reviewed policy maps those facts to `pass`, `warn`, `fail`, `error`, `skip`, or `escalate`.

The initial policy implementation should remain JSON Schema plus standard-library code while requirements are small. OPA/Conftest may be evaluated only when multiple modules or projects demonstrate policy duplication that Rego would reduce. Adoption requires policy tests, version pinning, failure semantics, and migration evidence.

Policy changes are security-sensitive. A pull request that changes both a check and its allowlist, threshold, or exception must expose that combined effect to review.

## Execution tiers

| Tier | Trigger | Intended work |
|---|---|---|
| Pre-flight | Local or before push | Formatting, schema validation, fast deterministic checks |
| Fast gate | Pull request | Relevant tests, workflow checks, bounded dependency and secret checks |
| Full gate | Main | Full tests, build/package, canonical evidence |
| Release gate | Release candidate | Same-artifact verification, provenance, installer checks |
| Deep gate | Schedule or explicit request | Fuzzing, mutation, expensive scans, reproducibility experiments |

No tool belongs to a tier by popularity alone. The module contract must record purpose, input, output, permissions, runner, timeout, failure behavior, evidence, and measured runtime.

## First consumer: ReleaseProof Core

ReleaseProof Core should be implemented before broad source intelligence because it has a concrete evidence target and can produce real failure data.

Version 0.1 is limited to:

1. release, tag, commit, workflow, and artifact identity;
2. immutable-release and artifact-attestation verification when supported;
3. SHA-256, file manifest, size, internal version, signature, and application identity;
4. one project-owned install, launch smoke, upgrade, and uninstall path;
5. structured claim-to-evidence mapping; and
6. a `bima-evidence` adapter with explicit scope and verdict.

Release claims must use stable IDs and evidence references. Free-form release notes may be generated for humans, but they are not proof by themselves.

GitHub-native immutable release and attestation capabilities should be evaluated before adding Cosign or custom signing orchestration. Signing and publishing remain explicit side-effect adapters outside core verification.

## Binary inspection and LLVM

LLVM is an opt-in native-binary adapter, not a mandatory runtime dependency.

Potential bounded uses:

- `llvm-readobj` for PE/COFF, ELF, or Mach-O headers and format-specific metadata;
- `llvm-size` for section-size evidence;
- `llvm-objdump` for object and linked-image inspection;
- `llvm-pdbutil` for PDB diagnostics on supported platforms.

LLVM does not prove installer behavior, registry state, application identity continuity, SBOM completeness, provenance, or release-claim truth. Installer and package adapters remain platform-specific.

Untrusted artifacts must be inspected in an isolated disposable environment. LLVM tooling is not treated as a hardened security boundary.

## Security adapter selection

Candidate tools remain replaceable adapters:

| Need | Initial candidate | Decision rule |
|---|---|---|
| Dependency vulnerabilities | OSV-Scanner | Prefer for supported manifests and lockfiles |
| Secret detection | Gitleaks | Evaluate on representative repositories |
| SBOM generation | Syft | Evaluate completeness on actual release artifacts |
| SBOM/artifact vulnerability scan | Grype or Trivy | Select through one comparative pilot |
| Source patterns | Semgrep | Enable only for supported project profiles |
| Deep code analysis | CodeQL, Infer, or Clang tooling | Project-specific need and runner budget required |

Do not run every candidate together by default. Overlap, false positives, setup time, network requirements, license, provenance, and evidence quality are part of the decision.

## Failure memory and routing

Failure memory begins before local-model work:

```text
failure packet
     |
confirmed root cause + verified fix
     |
project-owned incident
     |
shared root cause or repeated in 2+ projects?
     | yes
global known issue and machine-readable signature
```

Symptoms alone are not signatures. Every promoted rule links to reproduction and verification evidence. Expired rules must not silently remain authoritative.

Routing order:

1. exact deterministic rule;
2. reviewed historical retrieval;
3. optional small model;
4. strong agent or human;
5. deterministic re-verification.

## Local QA Coprocessor gate

The Local QA Coprocessor remains blocked until real consumers produce enough representative failures to prove a need.

Before activation it must:

- benchmark rules and retrieval as non-generative baselines;
- compare current small-model candidates rather than preselecting one winner;
- keep project and time-based held-out splits to reduce leakage;
- use constrained structured output plus semantic validation;
- operate in shadow mode before influencing routing;
- measure critical false negatives, hallucinated evidence, calibration, latency, RAM/VRAM, and frontier calls saved;
- abstain on low confidence, unknown domains, and security/release-critical ambiguity;
- remain optional so model absence cannot block deterministic verification.

The model never turns a deterministic failure into a pass and never receives unrestricted raw logs or repository secrets.

## Observability and storage

Start with retained structured summaries:

- execution duration and outcome;
- module and failure category;
- evidence and packet byte counts;
- machine-resolution and escalation rates;
- agent calls and estimated context avoided;
- cache restore/upload time where caching exists.

OpenTelemetry and a dashboard are deferred until multiple consumers need cross-repository aggregation. GitHub artifacts are evidence retention, not a permanent analytics database.

## Phased delivery

### Phase 0 — close the current baseline

- Exercise the existing reusable audit from a separate fixture repository with matched reviewed SHA pins.
- Retain and inspect consumer evidence.
- Decide repository protection and license.
- Integrate one real consumer without executing project code.

Acceptance: the current audit has published consumer proof and its stability label reflects actual evidence.

### Phase 1 — explicit project contract

- Define `bima-project.v1` through an ADR.
- Validate safe paths, bounded fields, capabilities, and runner requirements.
- Add advisory discovery with conflict reporting.

Acceptance: fixtures cover declared, detected, conflicting, unknown, malicious, and unsupported inputs.

### Phase 2 — ReleaseProof Core

- Select one real release project and one installer format.
- Implement the bounded Version 0.1 scope.
- Map results into canonical and execution evidence.

Acceptance: one release candidate produces inspectable source, artifact, installer, and claim evidence without an agent.

### Phase 3 — test and failure normalization

- Normalize project test results.
- Add known-failure registry and expiration policy.
- Record escalation metrics.

Acceptance: known failures route deterministically and unknown failures produce bounded packets.

### Phase 4 — measured adapters

- Pilot OSV and Gitleaks on representative repositories.
- Compare Syft plus Grype with Trivy for the selected artifact types.
- Add LLVM or diffoscope only where the ReleaseProof pilot needs them.

Acceptance: every retained adapter demonstrates unique value, bounded runtime, pinned provenance, and useful evidence.

### Phase 5 — historical quality intelligence

- Add performance baselines only for stable measurements.
- Add affected tests only where a trustworthy dependency graph exists.
- Run fuzzing, mutation, or reproducibility experiments outside the default pull-request gate.

Acceptance: thresholds include noise analysis and do not create unreviewed false-green paths.

### Phase 6 — optional local model

- Build a provenance-tracked benchmark from public and internal evidence.
- Correct dataset totals and define leakage-resistant splits.
- Run candidate models in shadow mode on the target hardware.

Acceptance: the selected path reduces total frontier-agent work after labeling and maintenance costs, while meeting the critical-failure policy.

### Phase 7 — fleet operation

- Add a project registry and cross-repository summaries.
- Evaluate telemetry and dashboard needs.

Acceptance: at least three consumers need the same aggregation and the storage/retention owner is defined.

## Success metrics

- machine-resolved task ratio;
- unknown-failure rate;
- agent calls and context bytes per successful task;
- median and p95 time to verified outcome;
- critical false-green count;
- false-positive and waived-finding rates;
- adapter setup and maintenance time;
- workflow runtime and artifact-storage growth;
- release claims verified from retained evidence;
- regressions or incidents caused by shared infrastructure.

Optimization targets must be established from a measured baseline. This RFC does not invent a percentage saving before consumer data exists.

## Compatibility and change control

- Schema and status-semantics changes require versioned migrations.
- Workflow callers pin reviewed immutable revisions.
- Tool versions and upstream provenance are recorded in implementation evidence, not frozen as prose claims in this RFC.
- Breaking project-profile changes require fixtures and migration notes.
- Each accepted implementation phase gets a focused ADR.
- Project-specific work remains in the owning repository.

## Risks

| Risk | Mitigation |
|---|---|
| Platform sprawl | One consumer and one bounded module at a time |
| Tool duplication | Comparative pilots and removal criteria |
| False confidence | Explicit scope, unknown state, deterministic verification |
| Untrusted project commands | Data-only PR checks and isolated trusted execution |
| Persistent runner compromise | No untrusted workloads on privileged persistent runners |
| Evidence schema churn | Versioned adapters and compatibility fixtures |
| Model maintenance exceeds savings | Shadow mode and total-cost metrics |
| Premature repository restructure | Add paths only when an implemented module needs them |

## Open decisions

1. Which repository and installer format will pilot ReleaseProof Core?
2. Which license will govern reusable infrastructure code?
3. Which solo-maintainer ruleset and bypass policy should protect `main`?
4. Where should long-term cross-project metrics live after artifact retention expires?
5. What measured threshold justifies OPA/Conftest over the existing policy code?

## References

- [Current architecture](../architecture/ARCHITECTURE.md)
- [Project integration contract](../architecture/PROJECT-CONTRACT.md)
- [Reusable workflow contract](../standards/WORKFLOW-CONTRACT.md)
- [Canonical evidence contract](../standards/EVIDENCE-CONTRACT.md)
- [Agent packet contract](../standards/AGENT-PACKET.md)
- [Security baseline](../standards/SECURITY-BASELINE.md)
- [Current next steps](../NEXT.md)
- [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations)
- [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
- [SLSA specification](https://slsa.dev/spec/v1.2/)
- [OASIS SARIF](https://www.oasis-open.org/committees/sarif/)
- [CycloneDX specification](https://cyclonedx.org/specification/overview/)
- [LLVM command guide](https://llvm.org/docs/CommandGuide/)
- [LLVM security scope](https://llvm.org/docs/Security.html)
