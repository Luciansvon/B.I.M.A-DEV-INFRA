import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "workflow_catalog.py"


def run(root, catalog="catalog/workflows.json"):
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT),
         "--root", str(root), "--catalog", catalog],
        cwd=ROOT, capture_output=True, text=True)


def write_fixture(root):
    workflow = root / ".github" / "workflows" / "sample.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text("name: Sample\non:\n  workflow_call:\n", encoding="utf-8")
    docs = root / "docs" / "standards" / "SAMPLE.md"
    docs.parent.mkdir(parents=True, exist_ok=True)
    docs.write_text("# Sample\n", encoding="utf-8")
    entry = {
        "id": "sample",
        "path": ".github/workflows/sample.yml",
        "status": "experimental",
        "docs": "docs/standards/SAMPLE.md",
        "consumers": ["owner/repo"],
        "sha256": hashlib.sha256(workflow.read_bytes()).hexdigest(),
        "summary": "Sample reusable workflow.",
    }
    catalog = root / "catalog" / "workflows.json"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(
        json.dumps({"schema": "bima-workflow-catalog.v1",
                    "schema_version": 1, "workflows": [entry]}, indent=2) + "\n",
        encoding="utf-8")
    return catalog, entry


class WorkflowCatalogTests(unittest.TestCase):
    def test_repository_catalog_matches_the_workflows(self):
        result = run(ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("workflows=4", result.stdout)

    def test_valid_fixture_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_tampered_workflow_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            (root / ".github" / "workflows" / "sample.yml").write_text(
                "name: Changed\non:\n  workflow_call:\n", encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("sha256 does not match", result.stderr)

    def test_duplicate_id_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, entry = write_fixture(root)
            document = json.loads(catalog.read_text(encoding="utf-8"))
            document["workflows"].append(dict(entry))
            catalog.write_text(json.dumps(document), encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("duplicate workflow id", result.stderr)

    def test_unknown_field_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, entry = write_fixture(root)
            document = json.loads(catalog.read_text(encoding="utf-8"))
            document["workflows"][0]["extra"] = True
            catalog.write_text(json.dumps(document), encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("entry keys", result.stderr)

    def test_non_reusable_workflow_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, entry = write_fixture(root)
            (root / ".github" / "workflows" / "sample.yml").write_text(
                "name: Sample\non: push\n", encoding="utf-8")
            entry["sha256"] = hashlib.sha256(
                (root / ".github" / "workflows" / "sample.yml").read_bytes()
            ).hexdigest()
            catalog.write_text(json.dumps(
                {"schema": "bima-workflow-catalog.v1", "schema_version": 1,
                 "workflows": [entry]}), encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("workflow_call", result.stderr)


if __name__ == "__main__":
    unittest.main()
