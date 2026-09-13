"""Create and verify deterministic artifact identity manifests."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


MAX_INPUT_BYTES = 1024 * 1024
MAX_ARTIFACTS = 64
MAX_ARTIFACT_BYTES = 1024 ** 4
CHUNK_BYTES = 1024 * 1024
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MEDIA_TYPE = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]{0,126}/[a-z0-9][a-z0-9!#$&^_.+-]{0,126}$"
)
ARTIFACT_FIELDS = {
    "artifact_id", "path", "media_type", "role", "sensitivity",
    "maximum_bytes", "retention",
}
MANIFEST_ARTIFACT_FIELDS = ARTIFACT_FIELDS | {"size_bytes", "sha256"}


class ArtifactIdentityError(ValueError):
    """Artifact identity input violates the supported contract."""


def canonical_bytes(value):
    return (json.dumps(
        value, ensure_ascii=True, allow_nan=False, sort_keys=True,
        separators=(",", ":")) + "\n").encode("utf-8")


def strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ArtifactIdentityError("duplicate JSON key")
            value[key] = item
        return value

    def constant(_):
        raise ArtifactIdentityError("non-finite JSON number")

    try:
        return json.loads(
            raw.decode("utf-8"), object_pairs_hook=pairs,
            parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ArtifactIdentityError("input is not strict UTF-8 JSON") from exc


def load_json(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ArtifactIdentityError(
            "input must be a regular file of at most 1048576 bytes")
    return strict_json(path.read_bytes())


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ArtifactIdentityError(f"{label} fields do not match the contract")


def _string(value, label, maximum=256):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ArtifactIdentityError(f"{label} is invalid")


def _identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ArtifactIdentityError(f"{label} is invalid")


def _sha(value, label):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ArtifactIdentityError(f"{label} must be SHA-256")


def _identity_fields(value, label):
    _exact(value["project"], {"id", "repository"}, f"{label} project")
    _identifier(value["project"]["id"], f"{label} project id")
    _string(value["project"]["repository"], f"{label} repository")
    _exact(value["subject"], {"revision", "dirty"}, f"{label} subject")
    revision = value["subject"]["revision"]
    if not isinstance(revision, str) or not REVISION.fullmatch(revision):
        raise ArtifactIdentityError(f"{label} subject revision must be a full Git SHA")
    if type(value["subject"]["dirty"]) is not bool:
        raise ArtifactIdentityError(f"{label} subject dirty must be boolean")
    _exact(value["policy"], {"revision", "sha256"}, f"{label} policy")
    _string(value["policy"]["revision"], f"{label} policy revision")
    _sha(value["policy"]["sha256"], f"{label} policy sha256")


def _relative_path(value, label):
    _string(value, label, 512)
    if "\\" in value or ":" in value or any(ord(char) < 32 for char in value):
        raise ArtifactIdentityError(f"{label} must be a canonical POSIX relative path")
    path = PurePosixPath(value)
    if (path.is_absolute() or value != path.as_posix()
            or not path.parts or any(part in {"", ".", ".."} for part in path.parts)):
        raise ArtifactIdentityError(f"{label} must be a canonical POSIX relative path")


def _retention(value, label):
    _exact(value, {"owner", "location", "minimum_days"}, label)
    _string(value["owner"], f"{label} owner")
    _string(value["location"], f"{label} location", 512)
    days = value["minimum_days"]
    if type(days) is not int or not 0 <= days <= 36500:
        raise ArtifactIdentityError(f"{label} minimum_days is invalid")


def _artifact(value, label, manifest=False):
    _exact(value, MANIFEST_ARTIFACT_FIELDS if manifest else ARTIFACT_FIELDS, label)
    _identifier(value["artifact_id"], f"{label} artifact_id")
    _relative_path(value["path"], f"{label} path")
    if not isinstance(value["media_type"], str) or not MEDIA_TYPE.fullmatch(
            value["media_type"]):
        raise ArtifactIdentityError(f"{label} media_type is invalid")
    if value["role"] not in {
            "primary", "checksum", "sbom", "signature", "attestation",
            "report", "auxiliary"}:
        raise ArtifactIdentityError(f"{label} role is invalid")
    if value["sensitivity"] not in {"public", "internal", "restricted"}:
        raise ArtifactIdentityError(f"{label} sensitivity is invalid")
    maximum = value["maximum_bytes"]
    if type(maximum) is not int or not 1 <= maximum <= MAX_ARTIFACT_BYTES:
        raise ArtifactIdentityError(f"{label} maximum_bytes is invalid")
    _retention(value["retention"], f"{label} retention")
    if manifest:
        size = value["size_bytes"]
        if type(size) is not int or not 0 <= size <= maximum:
            raise ArtifactIdentityError(f"{label} size_bytes is invalid")
        _sha(value["sha256"], f"{label} sha256")


def _artifacts(value, label, manifest=False):
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_ARTIFACTS:
        raise ArtifactIdentityError(f"{label} must contain 1 to 64 artifacts")
    for index, artifact in enumerate(value):
        _artifact(artifact, f"{label}[{index}]", manifest)
    ids = [artifact["artifact_id"] for artifact in value]
    paths = [artifact["path"] for artifact in value]
    if ids != sorted(set(ids)):
        raise ArtifactIdentityError(f"{label} must be unique and sorted by artifact_id")
    if len(paths) != len(set(paths)):
        raise ArtifactIdentityError(f"{label} paths must be unique")


def validate_request(value):
    _exact(value, {
        "schema", "manifest_id", "project", "subject", "policy", "artifacts",
    }, "request")
    if value["schema"] != "bima-artifact-manifest-request.v1":
        raise ArtifactIdentityError("unsupported request schema")
    _identifier(value["manifest_id"], "manifest id")
    _identity_fields(value, "request")
    _artifacts(value["artifacts"], "request artifacts")
    return value


def validate_manifest(value):
    _exact(value, {
        "schema", "manifest_id", "project", "subject", "policy",
        "request_sha256", "artifacts",
    }, "manifest")
    if value["schema"] != "bima-artifact-manifest.v1":
        raise ArtifactIdentityError("unsupported manifest schema")
    _identifier(value["manifest_id"], "manifest id")
    _identity_fields(value, "manifest")
    _sha(value["request_sha256"], "manifest request_sha256")
    _artifacts(value["artifacts"], "manifest artifacts", manifest=True)
    derived_request = {
        "schema": "bima-artifact-manifest-request.v1",
        "manifest_id": value["manifest_id"],
        "project": dict(value["project"]),
        "subject": dict(value["subject"]),
        "policy": dict(value["policy"]),
        "artifacts": [
            {key: artifact[key] for key in ARTIFACT_FIELDS}
            for artifact in value["artifacts"]
        ],
    }
    expected_request_sha = hashlib.sha256(canonical_bytes(derived_request)).hexdigest()
    if value["request_sha256"] != expected_request_sha:
        raise ArtifactIdentityError("manifest request_sha256 does not match its declarations")
    return value


def _validated_root(root):
    if root.is_symlink() or not root.is_dir():
        raise ArtifactIdentityError("root must be a regular directory, not a symlink")
    return root.resolve(strict=True)


def _candidate(root, relative):
    current = root
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            return current, "UNSAFE"
        if index < len(parts) - 1 and current.exists() and not current.is_dir():
            return current, "UNSAFE"
    try:
        resolved = current.resolve(strict=False)
    except (OSError, RuntimeError):
        return current, "UNSAFE"
    if not resolved.is_relative_to(root):
        return current, "UNSAFE"
    if not current.exists():
        return current, "MISSING"
    if not current.is_file():
        return current, "UNSAFE"
    return current, "PRESENT"


def _hash_file(path, maximum_bytes):
    before = path.stat(follow_symlinks=False)
    if before.st_size > maximum_bytes:
        raise ArtifactIdentityError("artifact exceeds its declared maximum_bytes")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
    after = path.stat(follow_symlinks=False)
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after:
        raise ArtifactIdentityError("artifact changed while hashing")
    return before.st_size, digest.hexdigest()


def create_manifest(request, root):
    validate_request(request)
    root = _validated_root(root)
    artifacts = []
    for declared in request["artifacts"]:
        path, state = _candidate(root, declared["path"])
        if state != "PRESENT":
            raise ArtifactIdentityError(
                f"artifact {declared['artifact_id']} is {state.lower()}")
        size, digest = _hash_file(path, declared["maximum_bytes"])
        artifacts.append({**declared, "size_bytes": size, "sha256": digest})
    return {
        "schema": "bima-artifact-manifest.v1",
        "manifest_id": request["manifest_id"],
        "project": dict(request["project"]),
        "subject": dict(request["subject"]),
        "policy": dict(request["policy"]),
        "request_sha256": hashlib.sha256(canonical_bytes(request)).hexdigest(),
        "artifacts": artifacts,
    }


def verify_manifest(manifest, root):
    validate_manifest(manifest)
    root = _validated_root(root)
    counts = {
        "declared": len(manifest["artifacts"]), "matched": 0,
        "missing": 0, "changed": 0, "unsafe": 0,
    }
    checks = []
    unresolved = []
    for expected in manifest["artifacts"]:
        path, state = _candidate(root, expected["path"])
        observed_size = None
        observed_digest = None
        status = state
        if state == "PRESENT":
            try:
                observed_size = path.stat(follow_symlinks=False).st_size
                if observed_size > expected["maximum_bytes"]:
                    status = "CHANGED"
                else:
                    observed_size, observed_digest = _hash_file(
                        path, expected["maximum_bytes"])
                    status = "MATCH" if (
                        observed_size == expected["size_bytes"]
                        and observed_digest == expected["sha256"]
                    ) else "CHANGED"
            except (ArtifactIdentityError, OSError):
                status = "UNSAFE"
        count_field = "matched" if status == "MATCH" else status.lower()
        counts[count_field] += 1
        if status != "MATCH":
            unresolved.append(expected["artifact_id"])
        checks.append({
            "artifact_id": expected["artifact_id"],
            "path": expected["path"],
            "status": status,
            "expected_size_bytes": expected["size_bytes"],
            "observed_size_bytes": observed_size,
            "expected_sha256": expected["sha256"],
            "observed_sha256": observed_digest,
        })
    if counts["unsafe"]:
        verdict, reason = "FAIL", "ARTIFACT_PATH_UNSAFE"
    elif counts["missing"]:
        verdict, reason = "FAIL", "ARTIFACT_MISSING"
    elif counts["changed"]:
        verdict, reason = "FAIL", "ARTIFACT_CHANGED"
    else:
        verdict, reason = "PASS", "ALL_ARTIFACTS_MATCH"
    return {
        "schema": "bima-artifact-verification.v1",
        "verdict": verdict,
        "reason_code": reason,
        "identity": {
            "manifest_id": manifest["manifest_id"],
            "project_id": manifest["project"]["id"],
            "repository": manifest["project"]["repository"],
            "subject_revision": manifest["subject"]["revision"],
            "subject_dirty": manifest["subject"]["dirty"],
        },
        "policy": dict(manifest["policy"]),
        "manifest_sha256": hashlib.sha256(canonical_bytes(manifest)).hexdigest(),
        "counts": counts,
        "checks": checks,
        "unresolved_artifacts": unresolved,
    }


def _write_output(output, filename, value):
    if any(path.is_symlink() for path in [output, *output.parents]):
        raise ArtifactIdentityError("output directory cannot be a symlink")
    output.mkdir(parents=True, exist_ok=True)
    if not output.is_dir():
        raise ArtifactIdentityError("output must be a directory")
    destination = output / filename
    if destination.is_symlink():
        raise ArtifactIdentityError("output file cannot be a symlink")
    if destination.exists():
        destination.unlink()
    destination.write_bytes(canonical_bytes(value))


def _reject_output_overlap(output, filename, root, relative_paths):
    root = _validated_root(root)
    destination = (output / filename).resolve(strict=False)
    if destination.is_relative_to(root):
        relative = destination.relative_to(root).as_posix()
        if relative in set(relative_paths):
            raise ArtifactIdentityError("output file cannot overwrite a declared artifact")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--request", type=Path, required=True)
    create.add_argument("--root", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--root", type=Path, required=True)
    verify.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "create":
            manifest = create_manifest(load_json(args.request), args.root)
            _reject_output_overlap(
                args.output, "manifest.json", args.root,
                [artifact["path"] for artifact in manifest["artifacts"]])
            _write_output(args.output, "manifest.json", manifest)
            print(
                "artifact-identity: CREATED; "
                f"created={len(manifest['artifacts'])}; "
                f"manifest_sha256={hashlib.sha256(canonical_bytes(manifest)).hexdigest()}")
            return 0
        manifest = load_json(args.manifest)
        report = verify_manifest(manifest, args.root)
        _reject_output_overlap(
            args.output, "verification.json", args.root,
            [artifact["path"] for artifact in manifest["artifacts"]])
        _write_output(args.output, "verification.json", report)
        print(
            f"artifact-identity: {report['verdict']}; "
            f"reason={report['reason_code']}; "
            f"matched={report['counts']['matched']}/{report['counts']['declared']}")
        return 0 if report["verdict"] == "PASS" else 1
    except (ArtifactIdentityError, OSError) as exc:
        print(f"artifact-identity: ERROR; {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
