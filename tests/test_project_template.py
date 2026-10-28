import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "bootstrap_project.py"
SHA = "a" * 40


def run(*arguments):
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), *arguments],
        cwd=ROOT, capture_output=True, text=True)


class ProjectBootstrapTests(unittest.TestCase):
    def test_bootstrap_fills_placeholders_and_records_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            result = run("--target", str(target), "--infra-ref", SHA,
                         "--project-name", "Sample Project")
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads(result.stdout)
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["infra_ref"], SHA)
            self.assertEqual(manifest["project_name"], "Sample Project")
            self.assertTrue(manifest["files"])

            for entry in manifest["files"]:
                path = target / entry["path"]
                data = path.read_bytes()
                self.assertEqual(entry["bytes"], len(data))
                self.assertNotRegex(data.decode("utf-8"), r"__[A-Z][A-Z0-9_]*__")

            readme = (target / "README.md").read_text(encoding="utf-8")
            self.assertIn("# Sample Project", readme)
            workflow = (target / ".github" / "workflows" /
                        "bima-shared-audit.yml").read_text(encoding="utf-8")
            self.assertEqual(workflow.count(SHA), 2)
            self.assertIn("policy-path: .bima/audit.json", workflow)

    def test_invalid_sha_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            result = run("--target", str(target), "--infra-ref", "abc",
                         "--project-name", "Sample")
            self.assertEqual(result.returncode, 2)
            self.assertIn("full lowercase commit SHA", result.stderr)
            self.assertFalse(target.exists())

    def test_non_empty_target_is_not_touched(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            sentinel = target / "keep.txt"
            sentinel.write_text("keep\n", encoding="utf-8")
            result = run("--target", str(target), "--infra-ref", SHA,
                         "--project-name", "Sample")
            self.assertEqual(result.returncode, 2)
            self.assertIn("target is not empty", result.stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep\n")
            self.assertEqual([path.name for path in target.iterdir()], ["keep.txt"])

    def test_control_characters_in_name_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            result = run("--target", str(target), "--infra-ref", SHA,
                         "--project-name", "Bad\nName")
            self.assertEqual(result.returncode, 2)
            self.assertIn("control characters", result.stderr)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
