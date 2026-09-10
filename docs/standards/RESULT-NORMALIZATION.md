# Result normalization v2

Status: **Executable Rust libtest adapter with DEV-INFRA hosted regression; consumer migration pending.**

## Scope

`result_normalizer.py` converts bounded Rust libtest text summaries into additive `bima-verification-result.v2` evidence. It preserves v1 evidence unchanged and never treats successful parsing as proof that tests passed.

The initial real source is AI-COLOR-COMPARE:

- successful native `cargo test` output from [run 34361196506](https://github.com/Luciansvon/AI-COLOR-COMPARE/actions/runs/34361196506), revision `534bb77461e1f475a096cb54954fb03176a210d6`: 29 passed, followed by two explicit zero-test suite summaries;
- sanitized TypeScript diagnostic fixture derived from [failed run 34084298571](https://github.com/Luciansvon/AI-COLOR-COMPARE/actions/runs/34084298571), revision `d0827b6b24dcb3956178ab8d8fe91fac4e42b65f`: TS2322, TS2362 and TS2363 in `src/color_science/rgb_analysis.ts`.

Fixtures retain only the minimum diagnostic meaning required to exercise the parser. They are not copies of full GitHub job logs. The TypeScript failure fixture is never attached to the Rust PASS result because it belongs to a different revision and command; cross-attempt evidence must not inherit another result's identity.

## Input contract

`bima-normalization-request.v1` binds:

- project ID and repository;
- exact subject revision and dirty state;
- required/optional check ID and expected test count;
- adapter ID;
- command identity and SHA-256;
- policy revision and SHA-256;
- OS, architecture and toolchain identity;
- attempt ID, sequence and equivalence key;
- native process exit code.
- expected SHA-256 for native output and optional same-attempt failure log.

The native-output and optional failure-log files are separate byte-hashed sources. Each is limited to 1 MiB and must be UTF-8. Their presence and bytes must match the request hashes before parsing. Unknown fields, adapters and malformed JSON fail closed. Committed `.log` fixtures are pinned to LF through `.gitattributes` so byte identity is stable across checkouts.

## Verdict rules

For the initial required-check adapter:

| Evidence | Verdict |
|---|---|
| Every parsed suite reports success, exit code is zero and observed tests equal the declared expectation | `PASS` |
| Parsed suite reports at least one failed test and process exit is nonzero | `FAIL` |
| Summary missing | `UNKNOWN` |
| Expected and observed test counts differ | `UNKNOWN` |
| Exit code and parsed summary disagree | `UNKNOWN` |
| Nonzero exit without a reported test failure | `UNKNOWN` |

Ignored tests count as observed but remain explicit. Filtered-out tests do not count as executed. Every suite summary remains in the result, including zero-test binary/doc-test suites. `FLAKY` is not an aggregate verdict: stability remains `unassessed` until equivalent attempts or a reviewed registry establish it.

The additive [known failure registry](KNOWN-FAILURE-REGISTRY.md) classifies exact reviewed diagnostic signatures separately. It does not rewrite the verdict or stability and always denies automatic retry.

## Failure diagnostics

The optional failure-log path currently extracts TypeScript diagnostics only when the caller proves it belongs to the same declared attempt. Output is capped at 50 records; paths are reduced to repository-relative `src/` or `tests/` paths where possible; messages are capped at 240 characters. ANSI control sequences, NUL bytes and common token/password patterns are removed or redacted.

Raw log lines, runner prefixes, timestamps, absolute workspace roots and unrelated output are not copied into v2. The evidence records source SHA-256 and byte size so approved native data can be traced separately under project retention policy.

This is sanitization for a narrow diagnostic format, not a universal secret scanner. Callers must still provide bounded, approved log input and must not upload private raw logs merely because this adapter exists.

## Outputs and compatibility

`result.json` uses `bima-verification-result.v2`. It separates:

- aggregate verdict;
- native attempt outcome and reason;
- applicability;
- stability;
- project/subject/check identity;
- command/policy/environment/attempt identity;
- per-suite counts;
- source digests;
- bounded diagnostics.

No `bima-evidence.v1`, execution-v1 or agent-packet-v1 schema, generator, status or path changes. A v2 consumer must opt in separately. Before any consumer pin changes, add successful/failing/malformed/missing-result fixtures, hosted evidence and an explicit rollback to the prior reviewed pin.

## CLI

```text
python -I automation/result_normalizer.py \
  --request <bima-normalization-request.v1.json> \
  --native-output <bounded-rust-output.log> \
  --failure-log <optional-bounded-diagnostic.log> \
  --output <trusted-output-directory>
```

Exit codes are `0=PASS`, `1=FAIL`, `2=UNKNOWN/contract error`, `3=BLOCKED`. The initial parser does not emit `BLOCKED`; execution providers supply that state when a required check cannot run or complete.
