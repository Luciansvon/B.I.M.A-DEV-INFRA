# Release template validation — 2026-10-28

Scope: prove the reusable release publication workflow (`.github/workflows/release.yml`) in DEV-INFRA, an external data-only fixture, and a real consumer. This validates publication mechanics only; it is not ReleaseProof provenance or release-QA evidence.

## DEV-INFRA dry run

- Merge: `587017f8723814e91f2937f16553bacc0974ae21` (PR #40).
- Runs: `40631258095` (push) and `40631274523` (manual dispatch), both success.
- Artifact `release-evidence-40631274523-1` records `assets=1`, `tag_status=404`, `dry_run=true`, `published=false`, `release_url=null`, and the asset SHA-256 `7b621fb26d83fc8494fd13825c8aa2c62bb2c6480bef13dc8784b5550ae84559`.
- No tag `v0.0.0-self-test` and no release existed after the runs.

## External fixture real publication

- Repository: `Luciansvon/B.I.M.A-DEV-INFRA-FIXTURE`, caller commit `b3e425b4e1d63190a9a38e319a14e2301105b954`.
- Run `40631449793` success; release `v0.0.1-fixture` is not a draft and not a prerelease.
- Tag points at `b3e425b4e1d63190a9a38e319a14e2301105b954`; asset `fixture-asset.txt` has size 34 and digest `sha256:0fe6f932f79bc738885475870192665617ad1f8e491c8de28329d5456a2f9d6b`.
- Evidence `release-evidence-40631449793-1` records the same SHA-256, `dry_run=false`, `published=true`.

## Existing-tag refusal

- Run `40631540228` dispatched the same tag again; it failed with `tag v0.0.1-fixture already exists; release tags are not overwritten` and exit code 2. No release was overwritten.

## AI-COLOR-COMPARE consumer adoption

- PR #15 merged as `87d7698`; the publish job calls the template at `587017f...`.
- The first dispatch from `main` (run `40632975258`) failed in `release-windows` before the template because `main` is already source version 0.3.11 while the legacy `release-v0.3.10.yml` guard requires 0.3.10. The `publish` job was skipped, so no wrong release was created. This is a pre-existing version-pinning defect in that legacy workflow, not a template failure.
- Rehearsal branch `rehearsal/release-v0.3.10` at `9e120861e08af5c6f61478a0b3db70e94e691504` (v0.3.10 source plus the adopted caller). Run `40633590558` succeeded.
- Release `v0.3.10-rc.1` is a prerelease, not a draft, with three assets. GitHub digests match the evidence artifact exactly:
  - `Studio-Color-QC-v0.3.10-Android-Pilot.apk` — 160091982 bytes, `sha256:62852ac5af24c9eb74611447b7d059ae2d239d6953fd26a3496d1a57f21ef7ec`
  - `Studio-Color-QC-v0.3.10-Windows-x64-Offline-Full-Setup.exe` — 223018503 bytes, `sha256:1c4c85be1331e8a4d95ff41574180948968a6d5485917ac55eb260260bb95ba5`
  - `Studio-Color-QC-v0.3.10-Windows-x64-Setup.exe` — 5340154 bytes, `sha256:15c892a9a1f02bff3fd6e5f4ec451ed85db8e5eec49bd482279dac64cf073d80`
- Evidence `release-evidence-40633590558-1` records `assets=3`, `tag_status=404`, `published=true`, `release_url=https://github.com/Luciansvon/AI-COLOR-COMPARE/releases/tag/v0.3.10-rc.1`.

## Boundaries

- The rehearsal ran from a branch cut at the v0.3.10 source, not from current `main`; the main path stays unproven until a future release adopts the template at the current source version.
- The template does not build, sign, notarize, attest or prove artifact provenance. It publishes the assets selected from the calling run and records their hashes.
- The fixture and rehearsal releases are deliberately public evidence, not production releases.
