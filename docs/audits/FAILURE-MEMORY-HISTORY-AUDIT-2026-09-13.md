# Failure Memory history audit — 2026-09-13

## Verdict

Five real shared-infrastructure failure/fix pairs are technically eligible as
Failure Memory candidates. None is activated in `failure-records/records.json`
because PRs #10, #25 and #26 have no independent review. Counting them before
that review would violate the failure-record contract.

Current production activation remains `0/100` active real records and `0/10`
held-out queries. Independent approval of all five candidates would move only
the record count to `5/100`; it would not authorize database creation or the
production retrieval benchmark.

## Audit scope

- All five failed GitHub Actions runs returned by `gh run list --status failure`
  on 2026-09-13.
- PR history, commits and review state for [#10], [#25] and [#26].
- Retained local security evidence in the [zizmor validation report].
- Successful hosted runs at the fixing revision or the merged `main` revision.
- Synthetic negative fixtures were excluded.

[#10]: https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/pull/10
[#25]: https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/pull/25
[#26]: https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/pull/26
[zizmor validation report]: VALIDATION-2026-09-09-ZIZMOR.md

## Candidate inventory

| Candidate | Failure and confirmed cause | Scoped fix | Re-verification | Review state |
|---|---|---|---|---|
| CAND-001 Dependabot cooldown | The initial real repository scan failed with zizmor exit 13 on `dependabot-cooldown`; `.github/dependabot.yml` had no cooldown. Evidence is retained in the [zizmor validation report]. | Add `cooldown.default-days: 7`; merged in [`a180c063`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/commit/a180c0633a9e48d289297eb8aae29e474160e62a). | [`34317637553`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34317637553): workflow lint and Ubuntu/Windows repository audit passed on merged `main`. | Pending independent review. |
| CAND-002 Local action syntax conflicts across linters | [`34469480213`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34469480213): zizmor rejected the GitHub-supported `./.github/actions/...` form and suggested `$/...`. [`34469803989`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34469803989): actionlint 1.7.12 rejected `$/...` because the action ref was missing. Both failures are one compatibility root cause, not two cases. | Keep `./...` and add the narrow `zizmor: ignore[self-repository]` annotation in [`32ba7892`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/commit/32ba789255a714a8800e807e7a68943d34bb39ec). | [`34470140936`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34470140936): preflight, actionlint and Ubuntu/Windows jobs passed on merged PR #25. | Pending independent review. |
| CAND-003 POSIX normalization destroys network-path identity | [`34707022884`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34707022884): Ubuntu resolved `//server/share` to `/server/share`, then attempted to create `/server`, producing `PermissionError` and one test error. The network-path guard ran after destructive normalization. | Reject raw `\\` and `//` prefixes before `Path.resolve()` in [`1103ac39`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/commit/1103ac3978441253251a9a818a4977fbdbdb350a). | [`34707772773`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34707772773): workflow lint plus all 111 tests on Ubuntu and Windows passed after merge. | Pending independent review. |
| CAND-004 Trusted bundle identifier drift | [`34707023160`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34707023160): launcher returned `DENY`, `TRUST_FILE_MISSING`, `verifier_launched=false`. The workflow used `dev-infra-repository-audit-v1`, while the committed bundle ID is `dev-infra-repository-audit.v1`. | Use the committed bundle ID and bind the workflow test to the bundle JSON in [`1103ac39`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/commit/1103ac3978441253251a9a818a4977fbdbdb350a). | [`34707772966`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34707772966): trusted launcher completed on merged `main`; verifier launched and its audit passed. | Pending independent review. |
| CAND-005 Pinact version-comment grammar | [`34707022884`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34707022884) and [`34707271646`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34707271646): pinact 4.1.1 rejected an absent comment and then `# trusted-launcher-v1`; only a recognized version-shaped label is accepted. These are two attempts at one root cause. | Change the full-SHA pin annotation to `# v1` in [`d409ea26`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/commit/d409ea264fe60d17eacdc2735007f0369f9c452c). | [`34707530700`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34707530700) and merged-main run [`34707772773`](https://github.com/Luciansvon/B.I.M.A-DEV-INFRA/actions/runs/34707772773): pinact and all other workflow gates passed. | Pending independent review. |

## Exclusions

- Two failed attempts caused by one confirmed cause are one record, not two.
- Synthetic malicious/malformed/missing-result fixtures are contract tests and
  do not count as real cases.
- GKI-0001 remains open. It is not an active failure-memory record until its fix
  is re-verified across the affected repositories and independently reviewed.
- Repository governance decisions and missing permissions are not failure/fix
  pairs.

## Activation boundary

The next valid action is an independent review of each candidate's failure,
cause, fix, scope and evidence. After approval, convert approved candidates to
canonical `bima-failure-record.v1` entries with distinct owner and reviewer
identities and run the record validator. Do not create held-out queries from
unapproved candidates, and do not create the production SQLite index below the
100-record gate.
