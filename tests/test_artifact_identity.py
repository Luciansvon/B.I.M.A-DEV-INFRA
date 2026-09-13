import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "artifact_identity.py"
FIXTURE = ROOT / "tests" / "fixtures" / "artifact-identity" / "request.json"
SPEC = importlib.util.spec_from_file_location("artifact_identity", SCRIPT)
artifact_identity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(artifact_identity)


class ArtifactIdentityTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.request["artifacts"][0]["path"] = "dist/application.bin"

    def _root(self, temporary, content=b"release-bytes-v1\x00"):
        root = Path(temporary) / "subject"
        (root / "dist").mkdir(parents=True)
        (root / "dist" / "application.bin").write_bytes(content)
        return root

    def test_create_manifest_hashes_declared_regular_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            manifest = artifact_identity.create_manifest(self.request, root)
            entry = manifest["artifacts"][0]
            self.assertEqual(entry["size_bytes"], 17)
            self.assertEqual(
                entry["sha256"],
                "cad9a06ff5bae6ddd35e04063b9d1ff560dd9e28df9740834153717552bc9684",
            )
            self.assertRegex(manifest["request_sha256"], r"^[0-9a-f]{64}$")

    def test_create_manifest_is_canonical_and_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            first = artifact_identity.create_manifest(self.request, root)
            second = artifact_identity.create_manifest(self.request, root)
            self.assertEqual(
                artifact_identity.canonical_bytes(first),
                artifact_identity.canonical_bytes(second),
            )

    def test_request_rejects_unknown_fields_and_noncanonical_paths(self):
        unknown = copy.deepcopy(self.request)
        unknown["extra"] = True
        with self.assertRaises(artifact_identity.ArtifactIdentityError):
            artifact_identity.validate_request(unknown)
        for path in ("../secret", "/absolute", "C:/windows", "dist\\app.bin", "dist//app.bin"):
            request = copy.deepcopy(self.request)
            request["artifacts"][0]["path"] = path
            with self.subTest(path=path), self.assertRaises(
                    artifact_identity.ArtifactIdentityError):
                artifact_identity.validate_request(request)

    def test_request_requires_sorted_ids_and_unique_paths(self):
        second = copy.deepcopy(self.request["artifacts"][0])
        second["artifact_id"] = "aaa"
        second["path"] = "dist/second.bin"
        request = copy.deepcopy(self.request)
        request["artifacts"].append(second)
        with self.assertRaises(artifact_identity.ArtifactIdentityError):
            artifact_identity.validate_request(request)
        request["artifacts"] = sorted(
            request["artifacts"], key=lambda value: value["artifact_id"])
        request["artifacts"][1]["path"] = request["artifacts"][0]["path"]
        with self.assertRaises(artifact_identity.ArtifactIdentityError):
            artifact_identity.validate_request(request)

    def test_create_rejects_missing_and_oversized_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            missing = copy.deepcopy(self.request)
            missing["artifacts"][0]["path"] = "dist/missing.bin"
            with self.assertRaises(artifact_identity.ArtifactIdentityError):
                artifact_identity.create_manifest(missing, root)
            oversized = copy.deepcopy(self.request)
            oversized["artifacts"][0]["maximum_bytes"] = 1
            with self.assertRaises(artifact_identity.ArtifactIdentityError):
                artifact_identity.create_manifest(oversized, root)

    def test_verify_matches_unchanged_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            manifest = artifact_identity.create_manifest(self.request, root)
            report = artifact_identity.verify_manifest(manifest, root)
            self.assertEqual(report["verdict"], "PASS")
            self.assertEqual(report["reason_code"], "ALL_ARTIFACTS_MATCH")
            self.assertEqual(report["counts"]["matched"], 1)
            self.assertEqual(report["unresolved_artifacts"], [])

    def test_verify_fails_when_artifact_bytes_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            manifest = artifact_identity.create_manifest(self.request, root)
            (root / "dist" / "application.bin").write_bytes(b"different")
            report = artifact_identity.verify_manifest(manifest, root)
            self.assertEqual(report["verdict"], "FAIL")
            self.assertEqual(report["reason_code"], "ARTIFACT_CHANGED")
            self.assertEqual(report["counts"]["changed"], 1)
            self.assertEqual(report["unresolved_artifacts"], ["application-binary"])

    def test_verify_reports_growth_beyond_declared_limit_as_changed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            request = copy.deepcopy(self.request)
            request["artifacts"][0]["maximum_bytes"] = 17
            manifest = artifact_identity.create_manifest(request, root)
            (root / "dist" / "application.bin").write_bytes(b"x" * 18)
            report = artifact_identity.verify_manifest(manifest, root)
            self.assertEqual(report["reason_code"], "ARTIFACT_CHANGED")
            self.assertEqual(report["counts"]["changed"], 1)
            self.assertEqual(report["checks"][0]["observed_size_bytes"], 18)
            self.assertIsNone(report["checks"][0]["observed_sha256"])

    def test_verify_fails_when_artifact_is_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            manifest = artifact_identity.create_manifest(self.request, root)
            (root / "dist" / "application.bin").unlink()
            report = artifact_identity.verify_manifest(manifest, root)
            self.assertEqual(report["reason_code"], "ARTIFACT_MISSING")
            self.assertEqual(report["counts"]["missing"], 1)

    @unittest.skipUnless(hasattr(Path, "symlink_to"), "symlink API unavailable")
    def test_symlink_artifact_fails_closed_when_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            manifest = artifact_identity.create_manifest(self.request, root)
            artifact = root / "dist" / "application.bin"
            target = root / "outside.bin"
            target.write_bytes(b"release-bytes-v1\x00")
            artifact.unlink()
            try:
                artifact.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            report = artifact_identity.verify_manifest(manifest, root)
            self.assertEqual(report["reason_code"], "ARTIFACT_PATH_UNSAFE")
            self.assertEqual(report["counts"]["unsafe"], 1)

    def test_manifest_rejects_impossible_size_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            manifest = artifact_identity.create_manifest(self.request, root)
            manifest["artifacts"][0]["size_bytes"] = (
                manifest["artifacts"][0]["maximum_bytes"] + 1)
            with self.assertRaises(artifact_identity.ArtifactIdentityError):
                artifact_identity.validate_manifest(manifest)
            manifest = artifact_identity.create_manifest(self.request, root)
            manifest["unknown"] = True
            with self.assertRaises(artifact_identity.ArtifactIdentityError):
                artifact_identity.validate_manifest(manifest)

    def test_manifest_request_digest_detects_metadata_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary)
            manifest = artifact_identity.create_manifest(self.request, root)
            manifest["artifacts"][0]["media_type"] = "application/zip"
            with self.assertRaisesRegex(
                    artifact_identity.ArtifactIdentityError, "request_sha256"):
                artifact_identity.validate_manifest(manifest)

    def test_strict_json_rejects_duplicate_and_nonfinite_values(self):
        with self.assertRaises(artifact_identity.ArtifactIdentityError):
            artifact_identity.strict_json(b'{"schema":"x","schema":"y"}')
        with self.assertRaises(artifact_identity.ArtifactIdentityError):
            artifact_identity.strict_json(b'{"value":NaN}')

    def test_cli_create_then_verify_and_preserves_fail_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            root = self._root(temporary)
            request = temporary / "request.json"
            request.write_bytes(artifact_identity.canonical_bytes(self.request))
            manifest_output = temporary / "manifest-output"
            create = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), "create", "--request", str(request),
                 "--root", str(root), "--output", str(manifest_output)],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(create.returncode, 0, create.stderr)
            manifest = manifest_output / "manifest.json"
            verify_output = temporary / "verify-output"
            verify = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), "verify", "--manifest", str(manifest),
                 "--root", str(root), "--output", str(verify_output)],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(verify.returncode, 0, verify.stderr)
            report = json.loads(
                (verify_output / "verification.json").read_text(encoding="utf-8"))
            self.assertEqual(report["verdict"], "PASS")
            (root / "dist" / "application.bin").write_bytes(b"tampered")
            failed = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), "verify", "--manifest", str(manifest),
                 "--root", str(root), "--output", str(verify_output)],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(failed.returncode, 1, failed.stderr)
            report = json.loads(
                (verify_output / "verification.json").read_text(encoding="utf-8"))
            self.assertEqual(report["verdict"], "FAIL")

    def test_cli_rejects_output_that_overwrites_declared_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            root = self._root(temporary)
            request_value = copy.deepcopy(self.request)
            request_value["artifacts"][0]["path"] = "output/manifest.json"
            output = root / "output"
            output.mkdir()
            (output / "manifest.json").write_bytes(b"existing-artifact")
            request = temporary / "request.json"
            request.write_bytes(artifact_identity.canonical_bytes(request_value))
            run = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), "create", "--request", str(request),
                 "--root", str(root), "--output", str(output)],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 2)
            self.assertIn("cannot overwrite a declared artifact", run.stderr)
            self.assertEqual((output / "manifest.json").read_bytes(), b"existing-artifact")


if __name__ == "__main__":
    unittest.main()
