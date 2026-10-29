import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "pin_freshness.py"
WORKFLOW = "name: Sample\non:\n  workflow_call:\n"


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def fixture(temporary, digest=None):
    root = Path(temporary)
    workflow = root / ".github" / "workflows" / "sample.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(WORKFLOW, encoding="utf-8")
    catalog = root / "catalog" / "workflows.json"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(json.dumps({"workflows": [{
        "path": ".github/workflows/sample.yml",
        "sha256": digest or hashlib.sha256(WORKFLOW.encode()).hexdigest()}]}),
        encoding="utf-8")
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-m", "fixture")
    revision = git(root, "rev-parse", "HEAD")
    return root, revision


def write_caller(root, revision, path=".github/workflows/sample.yml"):
    caller = root / ".github" / "workflows" / "caller.yml"
    caller.parent.mkdir(parents=True, exist_ok=True)
    caller.write_text(
        "name: Caller\non: push\njobs:\n  call:\n"
        "    uses: Luciansvon/B.I.M.A-DEV-INFRA/"
        f"{path}@{revision}\n", encoding="utf-8")


def run(root, *args):
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--root", str(root), *args],
        cwd=ROOT, capture_output=True, text=True)


class PinFreshnessTests(unittest.TestCase):
    def test_matching_pin_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, revision = fixture(temporary)
            write_caller(root, revision)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("refs=1", result.stdout)

    def test_catalog_digest_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, revision = fixture(temporary, digest="0" * 64)
            write_caller(root, revision)
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("pinned bytes differ", result.stderr)

    def test_unknown_revision_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = fixture(temporary)
            write_caller(root, "f" * 40)
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown revision or path", result.stderr)

    def test_uncataloged_workflow_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, revision = fixture(temporary)
            write_caller(root, revision, ".github/workflows/other.yml")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("not in the catalog", result.stderr)

    def test_no_pins_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = fixture(temporary)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("refs=0", result.stdout)

    def test_consumer_pin_matching_the_catalog_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, revision = fixture(Path(temporary) / "infra")
            consumer = Path(temporary) / "consumer"
            consumer.mkdir()
            write_caller(consumer, revision)
            result = run(root, "--consumer-root", str(consumer))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("refs=1", result.stdout)

    def test_consumer_pin_with_stale_bytes_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, revision = fixture(Path(temporary) / "infra")
            workflow = root / ".github" / "workflows" / "sample.yml"
            workflow.write_text(
                "name: Sample\non:\n  workflow_call:\n    inputs:\n"
                "      extra:\n        type: string\n", encoding="utf-8")
            catalog = root / "catalog" / "workflows.json"
            catalog.write_text(json.dumps({"workflows": [{
                "path": ".github/workflows/sample.yml",
                "sha256": hashlib.sha256(workflow.read_bytes()).hexdigest()}]}),
                encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-m", "reviewed change")
            consumer = Path(temporary) / "consumer"
            consumer.mkdir()
            write_caller(consumer, revision)
            result = run(root, "--consumer-root", str(consumer))
            self.assertEqual(result.returncode, 2)
            self.assertIn("pinned bytes differ", result.stderr)

    def test_consumer_pin_with_unknown_revision_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, _ = fixture(Path(temporary) / "infra")
            consumer = Path(temporary) / "consumer"
            consumer.mkdir()
            write_caller(consumer, "f" * 40)
            result = run(root, "--consumer-root", str(consumer))
            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown revision or path", result.stderr)


if __name__ == "__main__":
    unittest.main()
