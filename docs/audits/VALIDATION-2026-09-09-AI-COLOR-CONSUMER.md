# AI-COLOR-COMPARE consumer validation — 2026-09-09

## Scope

Real-project integration evidence for the beta `repository-audit` reusable workflow. AI-COLOR-COMPARE already consumed the initial workflow at infrastructure commit `77432e1d990e576b6e964565c8dc9a248db42d69`; this validation upgrades both pins to reviewed infrastructure commit `dc7a96cf885f41bd665270c4a77ef0e7c12d313b` and proves the current canonical-evidence contract. Only the caller workflow changed. No application source, release configuration, or operator behavior changed.

## Previous consumer evidence

AI-COLOR-COMPARE main revision [`d3e9423ba9c4d4d6023671ceed4fdb8a26186968`](https://github.com/Luciansvon/AI-COLOR-COMPARE/commit/d3e9423ba9c4d4d6023671ceed4fdb8a26186968) ran the shared audit successfully in run [`34348097292`](https://github.com/Luciansvon/AI-COLOR-COMPARE/actions/runs/34348097292): 213 files, 4 supported local links, and 0 findings. The downloaded artifact contained only `result.json` and `report.md` because the pinned infrastructure revision preceded canonical evidence and agent-packet support.

## Upgrade subject

- Consumer pull request: [AI-COLOR-COMPARE #13](https://github.com/Luciansvon/AI-COLOR-COMPARE/pull/13)
- Pin-update commit: `5787b78b3515a9ff9e7c9b59b1bd4fa5a222978e`
- Consumer main commit: [`534bb77461e1f475a096cb54954fb03176a210d6`](https://github.com/Luciansvon/AI-COLOR-COMPARE/commit/534bb77461e1f475a096cb54954fb03176a210d6)
- Reviewed infrastructure pin in both caller locations: `dc7a96cf885f41bd665270c4a77ef0e7c12d313b`

## Pull-request evidence

All three project checks passed before merge:

- shared audit run [`34359695471`](https://github.com/Luciansvon/AI-COLOR-COMPARE/actions/runs/34359695471): 7 seconds;
- application CI run [`34359693956`](https://github.com/Luciansvon/AI-COLOR-COMPARE/actions/runs/34359693956): 6 minutes 30 seconds;
- Windows installer smoke run [`34359694084`](https://github.com/Luciansvon/AI-COLOR-COMPARE/actions/runs/34359694084): 12 minutes 40 seconds.

The downloaded pull-request audit artifact contained `result.json`, `report.md`, `canonical.json`, `execution.json`, and `canonical.sha256`. It audited synthetic merge revision `c168554bfb5041508428fa61861398c3b5030c18`: 213 files, 4 supported local links, 0 findings, canonical SHA-256 `61b2870a2028db40bc06b63ef61796f05eb751547841f17752aec520b9104ae9`, and no pass-path agent packet.

The installer artifact ID `10107818745` contained `Studio Color QC_0.3.9_x64-setup.exe`: 5,341,450 bytes with SHA-256 `1594b49b3136e12ae46bcbc835391c200d53cadef9b75148efb6b8d6e88ba89d`. This proves the smoke workflow produced an installer; it does not constitute manual GUI or operator acceptance.

## Main evidence

The post-merge shared audit run [`34361197673`](https://github.com/Luciansvon/AI-COLOR-COMPARE/actions/runs/34361197673) audited exact clean main revision `534bb77461e1f475a096cb54954fb03176a210d6`:

- status: `pass`;
- Python: `3.13.15`;
- files checked: `213`;
- supported local links checked: `4`;
- findings: `0`;
- validator SHA-256: `4820e569910dbd41c5765e4d291a9e3600f2ebe67a4d93a017f0ba5a04e05805`;
- policy SHA-256: `c5e5b99cf78377356497c49cd3fb6217f81fd263cde1bd677ede58b5b11a436f`;
- canonical evidence SHA-256: `a9be9b3aeca9fbba32d72e2b02f972ba2ee5a0bbf726a684664551ede6dbd97c`;
- agent packet files: `0`, as required for a passing result.

Artifact ID `10107876905` retains the complete evidence set through 2026-09-23. Application CI run [`34361196506`](https://github.com/Luciansvon/AI-COLOR-COMPARE/actions/runs/34361196506) also passed on the exact main revision in 5 minutes 45 seconds. Its Node.js 20 compatibility annotation concerns project-owned Action versions and is not a repository-audit failure.

## Local evidence and boundary

The dirty Windows checkout also passed the current auditor with 213 files, 4 supported local links, and 0 findings. Its canonical hash is not compared with hosted evidence because dirty state and revision are semantic fields. The local policy byte hash also differed from hosted Ubuntu, consistent with checkout line-ending conversion; AI-COLOR-COMPARE should add an explicit text-normalization policy before claiming cross-platform byte-hash equality.

This integration proves one real repository can consume the beta contract as data and receive current evidence. It does not prove application correctness, visual color accuracy, operator acceptance, secrets scanning, broad ecosystem compatibility, or stable status.
