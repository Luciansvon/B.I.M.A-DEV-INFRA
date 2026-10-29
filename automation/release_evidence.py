"""Validate the release evidence document written by the release workflow.

The schema is permissive about empty strings, so this validator is stricter
where an empty value would make the evidence meaningless (title, URLs). It
never publishes, downloads or re-hashes artifacts.
"""

import argparse
import json
from pathlib import Path
import re
import sys


MAX_INPUT_BYTES = 1024 * 1024
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z][0-9A-Za-z.-]*)?$")
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
URL = re.compile(r"^https?://[^\s/]+(?:/[^\s]*)?$")
EVIDENCE_FIELDS = {
    "schema", "schema_version", "tag", "title", "target_sha", "prerelease",
    "dry_run", "published", "release_url", "run_url", "assets",
}
ASSET_FIELDS = {"name", "size", "sha256"}


class ReleaseEvidenceError(ValueError):
    """Release evidence does not match the bima-release-evidence.v1 contract."""


def strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ReleaseEvidenceError("duplicate JSON key")
            value[key] = item
        return value

    def constant(_):
        raise ReleaseEvidenceError("non-finite JSON number")

    try:
        return json.loads(
            raw.decode("utf-8"), object_pairs_hook=pairs,
            parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ReleaseEvidenceError("input is not strict UTF-8 JSON") from exc


def load_document(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ReleaseEvidenceError(
            "input must be a regular file within the byte limit")
    return strict_json(path.read_bytes())


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ReleaseEvidenceError(f"{label} fields do not match the v1 contract")


def _string(value, label, maximum=512):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ReleaseEvidenceError(f"{label} is invalid")


def _url(value, label):
    _string(value, label, 2048)
    if not URL.fullmatch(value):
        raise ReleaseEvidenceError(f"{label} is not an http(s) URL")


def validate_evidence(value):
    _exact(value, EVIDENCE_FIELDS, "release evidence")
    if value["schema"] != "bima-release-evidence.v1":
        raise ReleaseEvidenceError("unsupported release evidence schema")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ReleaseEvidenceError("schema_version must be integer 1")
    if not isinstance(value["tag"], str) or not TAG.fullmatch(value["tag"]):
        raise ReleaseEvidenceError("tag is not vX.Y.Z or vX.Y.Z-prerelease")
    _string(value["title"], "title")
    if not isinstance(value["target_sha"], str) or not COMMIT_SHA.fullmatch(
            value["target_sha"]):
        raise ReleaseEvidenceError("target_sha must be a full lowercase commit SHA")
    for field in ("prerelease", "dry_run", "published"):
        if type(value[field]) is not bool:
            raise ReleaseEvidenceError(f"{field} must be boolean")
    _url(value["run_url"], "run_url")
    if value["release_url"] is not None:
        _url(value["release_url"], "release_url")

    # A dry run publishes nothing; a published release must carry its URL.
    if value["dry_run"] and (value["published"] or value["release_url"] is not None):
        raise ReleaseEvidenceError("dry run cannot record a publication")
    if value["published"] and value["release_url"] is None:
        raise ReleaseEvidenceError("published release requires a release_url")

    assets = value["assets"]
    if not isinstance(assets, list) or not assets:
        raise ReleaseEvidenceError("assets must be a non-empty array")
    names = []
    for asset in assets:
        _exact(asset, ASSET_FIELDS, "release asset")
        _string(asset["name"], "asset name", 256)
        if type(asset["size"]) is not int or asset["size"] < 1:
            raise ReleaseEvidenceError("asset size must be a positive integer")
        if not isinstance(asset["sha256"], str) or not SHA256.fullmatch(
                asset["sha256"]):
            raise ReleaseEvidenceError("asset sha256 must be 64 lowercase hex characters")
        names.append(asset["name"])
    if len(names) != len(set(names)):
        raise ReleaseEvidenceError("asset names must be unique")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        evidence = validate_evidence(load_document(args.input))
    except (ReleaseEvidenceError, OSError) as exc:
        print(f"release-evidence: fail: {exc}")
        return 2
    print(f"release-evidence: pass; assets={len(evidence['assets'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
