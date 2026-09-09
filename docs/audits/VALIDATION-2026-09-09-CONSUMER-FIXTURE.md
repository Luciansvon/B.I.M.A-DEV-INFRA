# External consumer fixture validation — 2026-09-09

## Scope

Phase 0 consumer proof for the beta `repository-audit` reusable workflow. A separate public, data-only repository calls the published workflow without copying its implementation or executing project code. This validates the cross-repository interface, matching reviewed SHA pins, least-privilege caller, policy input, evidence upload, and pass-path packet behavior. It is not real project adoption, application testing, or production-readiness evidence.

## Published subjects

- Infrastructure commit: [`cb220412bf3d7be0e67cc364572eaf0183cda286`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/commit/cb220412bf3d7be0e67cc364572eaf0183cda286)
- Consumer repository: [`Luciansvon/B.I.M.A-DEV-INFRA-FIXTURE`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA-FIXTURE)
- Consumer pull request: [#1](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA-FIXTURE/pull/1)
- Consumer main commit: [`68af54df8610b14bdd2954bc079317dca4b1e2a6`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA-FIXTURE/commit/68af54df8610b14bdd2954bc079317dca4b1e2a6)
- Main workflow run: [`34357477215`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA-FIXTURE/actions/runs/34357477215)
- Evidence artifact ID: `10106348389`, retained by GitHub through 2026-09-23

## Pin and trust-boundary evidence

The committed consumer workflow contains the reviewed infrastructure SHA exactly twice:

```text
workflow reference -> cb220412bf3d7be0e67cc364572eaf0183cda286
infra-ref input    -> cb220412bf3d7be0e67cc364572eaf0183cda286
```

The main run log recorded the same SHA for the reusable-workflow call, `infra-ref` environment value, infrastructure fetch, object verification, and checkout. The caller grants only `contents: read`, supplies no secrets or executable command inputs, and uses GitHub-hosted Ubuntu execution.

## Hosted evidence

The pull-request run [`34357359204`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA-FIXTURE/actions/runs/34357359204) passed before merge. The post-merge main run then audited exact consumer revision `68af54df8610b14bdd2954bc079317dca4b1e2a6` with a clean working tree:

- status: `pass`;
- Python: `3.13.15`;
- files checked: `5`;
- supported local links checked: `0`;
- findings: `0`;
- validator SHA-256: `4820e569910dbd41c5765e4d291a9e3600f2ebe67a4d93a017f0ba5a04e05805`;
- policy SHA-256: `807ae5f88e4a93c764df99cbe6567d5ca159b337249a171a093162acded00ce0`;
- canonical evidence SHA-256: `9e2f637b2d6291783165e67caeb291d30fcdb42c1b66f77929f5629e8bdfe923`;
- agent packet files: `0`, as required for a passing result.

The downloaded artifact contained `result.json`, `report.md`, `canonical.json`, `execution.json`, and `canonical.sha256`. The report states the exact audit boundary: required files, file sizes, strict JSON, and supported inline local Markdown links. It explicitly does not claim secrets scanning, workflow security analysis, or application testing.

## Stability decision

The external interface is promoted from `experimental` to `beta`. It is not `stable`: only a synthetic data-only fixture has consumed it, and compatibility under a real project's repository shape and operating constraints is still unproven.

## Remaining Phase 0 work

- activate the selected `main` ruleset and bypass policy;
- choose an explicit repository license;
- integrate one real project through the pinned workflow and policy;
- retain and inspect that project's evidence before considering stable status.
