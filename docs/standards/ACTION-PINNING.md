# GitHub Action pinning contract

## Identity

Tool: pinact v4.1.1. Stability: **experimental**. Purpose: reject mutable GitHub Action and reusable-workflow references before commit or hosted execution.

## Enforcement mode

The prek hook runs:

```text
pinact run --fix=false --no-api <selected workflow/action files>
```

This mode is read-only and offline. It requires remote `uses:` references to contain a 40-character commit SHA. Local actions and Docker references remain outside that check. Prek selects the same workflow and local Action paths documented in the workflow-schema contract.

Pinact's default command edits files and can call GitHub APIs; neither behavior is allowed in the automatic pre-flight. Version updates remain reviewable dependency-maintenance work, currently proposed by Dependabot for GitHub Actions.

## GitHub adapter and evidence

The existing workflow-lint job downloads the official v4.1.1 Linux amd64 archive, verifies SHA-256 `d1cffebe5704b74e2e5f8a864efb9f7e54768972dc686188c008033fb1797841`, and extracts only the `pinact` binary into the ephemeral runner directory. `task preflight` records the version and hook result in `.artifacts/prek.log`.

The job retains `contents: read`, receives no secrets, makes no pinact API request, and creates no commit. A nonzero pinact result fails the hook and job.

## Local compatibility

Pinact publishes Windows, Linux, and macOS binaries. Local users install v4.1.1 on `PATH`; Docker is not required. The Windows amd64 archive SHA-256 is `88db480a3f8833d7233b482a72c97308df558ebceb0d3214775889239901f6a9`.

## Boundary

Offline syntax checking proves only that a full SHA is present. It does not prove that the SHA belongs to the named repository, matches the version comment, meets a release-age policy, or is trustworthy. Those checks require controlled GitHub API access and are not silently implied by this baseline.
