# Artifact Identity Contract v1

Status: **beta shared contract**
Implementation: `automation/artifact_identity.py`

## Purpose

Bind a declared artifact set to exact bytes before testing, promotion, signing,
or publication. The contract hashes files; it does not build, execute, sign,
upload, attest, or publish them.

```text
final artifact bytes
        |
        v
manifest.json -- SHA-256 + size + subject + policy
        |
        +--> test consumes and verifies the manifest
        |
        +--> publish consumes and verifies the same manifest
```

A second successful verification proves that the local bytes still match the
manifest. It does not prove application behavior, provenance, signature
validity, upload success, or remote retention.

## Commands

```text
python -I automation/artifact_identity.py create \
  --request request.json --root SUBJECT_ROOT --output OUTPUT_ROOT

python -I automation/artifact_identity.py verify \
  --manifest manifest.json --root SUBJECT_ROOT --output OUTPUT_ROOT
```

`create` writes `manifest.json`. `verify` always writes `verification.json`
for a valid manifest, returning exit `0` for `PASS`, `1` for identity failure,
and `2` for invalid input or an operational error.

## Inputs

`bima-artifact-manifest-request.v1` declares:

- manifest, project, repository, exact Git subject, and trusted policy identity;
- 1–64 unique artifacts sorted by `artifact_id`;
- canonical POSIX-relative path, maximum size, media type, and role;
- owning retention authority/location and sensitivity classification.

Supported roles are `primary`, `checksum`, `sbom`, `signature`, `attestation`,
`report`, and `auxiliary`. Retention metadata is descriptive; the tool does not
create or enforce remote retention.

## Outputs

`bima-artifact-manifest.v1` adds exact byte size and SHA-256 for every artifact,
plus the canonical request digest. `bima-artifact-verification.v1` binds its
result to the manifest digest and records every artifact as `MATCH`, `MISSING`,
`CHANGED`, or `UNSAFE`.

Overall reasons:

| Verdict | Reason |
|---|---|
| `PASS` | `ALL_ARTIFACTS_MATCH` |
| `FAIL` | `ARTIFACT_PATH_UNSAFE` |
| `FAIL` | `ARTIFACT_MISSING` |
| `FAIL` | `ARTIFACT_CHANGED` |

Unsafe wins over missing, which wins over changed. All unresolved artifact IDs
remain visible.

## Security and limits

- Strict UTF-8 JSON, exact fields, bounded input, and no non-finite numbers.
- Roots, inputs, outputs, artifact files, and path components must not be
  symlinks. Artifact paths cannot be absolute, contain `..`, backslashes,
  drive prefixes, or escape the declared root.
- Only regular files are hashed, in bounded streaming chunks. Each artifact
  has an explicit maximum size, capped by the contract at 1 TiB.
- File identity, size, and modification time are checked before and after
  hashing to detect concurrent changes.
- No network access, credentials, model calls, command execution, or recursive
  directory hashing.

The tool is an identity verifier, not a sandbox. Run untrusted builds and
binaries only in an independently approved execution boundary.

## Same-artifact rule

The final byte-changing transformation—packaging or signing—must happen before
manifest creation. Test and publication adapters must receive the same
`manifest_sha256`, re-run verification immediately before their operation, and
retain both verification reports. Any byte change requires a new manifest and
re-verification; copying a filename is not identity proof.

## Compatibility

This is additive. Existing evidence/result contracts and consumer pins remain
unchanged. A consumer opts in only after its final artifact path and lifecycle
are known. Release, signing, attestation, and remote-publication adapters remain
separate future capabilities with their own authorization and evidence.
