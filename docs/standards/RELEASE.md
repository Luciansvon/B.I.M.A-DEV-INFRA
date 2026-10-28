# Release publication workflow template

Status: **experimental**. Publication only: the caller builds and tests; this template validates and publishes.

## Identity

Name: `.github/workflows/release.yml`. Purpose: publish one GitHub release from the build artifacts of the calling run, with an explicit target commit, a new tag, a reviewed notes file, and retained evidence.

## Triggers

`workflow_call` only. Callers choose their own events and should trigger from a protected branch or tag. Manual/API invocation follows the caller.

## Inputs

| Input | Required | Type | Default | Description |
|---|---:|---|---|---|
| `tag` | yes | string | | New tag; `vX.Y.Z` with an optional `-prerelease` suffix |
| `title` | yes | string | | Release title |
| `notes-file` | yes | string | | Repository-relative regular file with the release notes |
| `target-sha` | yes | string | | Full 40-character commit SHA that the new tag must point at |
| `artifact-pattern` | yes | string | | Glob selecting only release artifacts produced by this run |
| `prerelease` | no | boolean | `false` | Mark the release as a prerelease |
| `dry-run` | no | boolean | `false` | Validate inputs, artifacts and tag policy without creating a release or tag |
| `artifact-name` | no | string | `release-evidence` | Unique evidence artifact prefix per call |

## Outputs

| Output | Type | Description |
|---|---|---|
| `release-url` | string | Published release URL; empty on dry-run |
| `evidence-artifact-id` | string | Uploaded evidence artifact ID |

## Runner

GitHub-hosted `ubuntu-24.04`, no labels or hardware requirements. Builds stay in the caller; Windows and macOS artifacts publish from this Linux job. A single caller cannot use this template on a Windows-only plan.

## Permissions

The caller's publishing job must grant `contents: write`. The called workflow declares `contents: read` at workflow level and `contents: write` only on the publish job. No secrets, OIDC, `actions: write` or `pull-requests: write`.

## Execution limits

15 minutes, no retries, no concurrency group. Release publication is not retried automatically because a failed attempt can leave a draft release behind.

## Evidence

`release.json` records the tag, title, target SHA, prerelease flag, dry-run flag, published flag, release URL, run URL, and each asset's name, size and SHA-256. `release-validation.txt` records the selected asset count, resolved notes path and tag status. Both are retained for 14 days. The upload uses `if-no-files-found: warn` so an earlier failure is not masked by a missing artifact.

## Failure contract

- Invalid tag, target SHA or notes path, no selected assets, duplicate asset names, or empty assets fail before any write.
- An existing tag fails closed; release tags are never overwritten.
- `gh` and API failures fail closed, including an unreadable tag status.
- Dry-run performs every validation and writes evidence, but creates no release or tag.
- Publication creates a draft release first and publishes it only after every asset uploads, so a partial upload stays invisible.
- A failure after the draft exists leaves the draft (and possibly the tag); delete both before retrying. The job log is the failure evidence.

## Security

- The caller checkout is untrusted data; the template never executes project code.
- `persist-credentials: false`; release writes use the job-scoped `GITHUB_TOKEN`.
- Artifacts are downloaded from the same run, hashed, and uploaded as evidence; no downloaded file is executed.
- The template does not sign, attest, rebuild or prove artifact provenance.

## Compatibility

Callers pin a full DEV-INFRA commit SHA in `uses:`. Keep the release tag and the source version in sync in the caller; this template cannot know the project's version files. Immutable releases depend on the repository setting; the tag guard is a workflow-level policy, not a platform guarantee. Version bumps, tag naming, notes authoring and asset naming stay project-owned.

Example caller job:

```yaml
publish:
  needs: [build]
  permissions:
    contents: write
  uses: Luciansvon/B.I.M.A-DEV-INFRA/.github/workflows/release.yml@<40-hex-sha>
  with:
    tag: v1.2.3
    title: Product v1.2.3
    notes-file: RELEASE_v1.2.3.md
    target-sha: ${{ github.sha }}
    artifact-pattern: '*-v1.2.3'
```

## Boundaries

This template does not build or test, bump versions, generate notes, sign or notarize binaries, produce SBOMs or attestations, verify that asset names match the tag, or enforce that the caller ran from a protected ref. It publishes exactly the artifacts selected from the calling run and cannot prove which commit produced them. The SHA-256 values in `release.json` are evidence, not a signed checksum manifest.

## Self-test

`.github/workflows/release-template-self-test.yml` runs on `main` pushes and manual dispatch. It uploads one fixture asset and calls this workflow with `dry-run: true`, so artifact download, input and tag validation, hashing, the job summary and evidence upload are hosted-proven without creating a release. Real publication is proven in the external consumer fixture; each consumer's first real release proves its own caller wiring.
