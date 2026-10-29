import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "workflow_catalog.py"
DOCUMENTATION = """# Sample

## Identity
Sample workflow.
## Triggers
workflow_call only.
## Inputs
None.
## Outputs
None.
## Runner
ubuntu-24.04.
## Permissions
contents: read.
## Execution limits
Ten minute job timeout.
## Evidence
Uploaded artifact.
## Failure contract
Non-zero exit on failure.
## Security
Pinned actions only.
## Compatibility
Version 1 is additive.
"""


def run(root, catalog="catalog/workflows.json"):
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT),
         "--root", str(root), "--catalog", catalog],
        cwd=ROOT, capture_output=True, text=True)


def write_catalog(root, entry):
    catalog = root / "catalog" / "workflows.json"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(
        json.dumps({"schema": "bima-workflow-catalog.v1",
                    "schema_version": 1, "workflows": [entry]}, indent=2) + "\n",
        encoding="utf-8")
    return catalog


def rewrite_workflow(root, entry, text):
    workflow = root / ".github" / "workflows" / "sample.yml"
    workflow.write_text(text, encoding="utf-8")
    entry["sha256"] = hashlib.sha256(workflow.read_bytes()).hexdigest()
    write_catalog(root, entry)


def write_fixture(root):
    workflow = root / ".github" / "workflows" / "sample.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text("name: Sample\non:\n  workflow_call:\n", encoding="utf-8")
    docs = root / "docs" / "standards" / "SAMPLE.md"
    docs.parent.mkdir(parents=True, exist_ok=True)
    docs.write_text(DOCUMENTATION, encoding="utf-8")
    audit = root / "docs" / "audits" / "VALIDATION-2026-01-01.md"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text("Consumer: `owner/repo`.\n", encoding="utf-8")
    entry = {
        "id": "sample",
        "path": ".github/workflows/sample.yml",
        "status": "experimental",
        "docs": "docs/standards/SAMPLE.md",
        "consumers": ["owner/repo"],
        "sha256": hashlib.sha256(workflow.read_bytes()).hexdigest(),
        "summary": "Sample reusable workflow.",
    }
    return write_catalog(root, entry), entry


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

    def test_uncataloged_reusable_workflow_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            (root / ".github" / "workflows" / "extra.yml").write_text(
                "name: Extra\non:\n  workflow_call:\n", encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("reusable workflow is not in the catalog", result.stderr)

    def test_non_reusable_workflow_is_not_required_in_catalog(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            (root / ".github" / "workflows" / "ci.yml").write_text(
                "name: CI\non: push\n", encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_input_documentation_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, entry = write_fixture(root)
            rewrite_workflow(
                root, entry,
                "name: Sample\non:\n  workflow_call:\n    inputs:\n"
                "      missing-input:\n        type: string\n")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("docs must name input `missing-input`", result.stderr)

    def test_missing_output_documentation_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, entry = write_fixture(root)
            rewrite_workflow(
                root, entry,
                "name: Sample\non:\n  workflow_call:\n    outputs:\n"
                "      missing-output:\n        value: ${{ jobs.a.outputs.b }}\n")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("docs must name output `missing-output`", result.stderr)

    def test_missing_contract_section_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            docs = root / "docs" / "standards" / "SAMPLE.md"
            docs.write_text(
                DOCUMENTATION.replace("## Evidence\nUploaded artifact.\n", ""),
                encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("docs must document sections: Evidence", result.stderr)

    def test_empty_contract_section_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            docs = root / "docs" / "standards" / "SAMPLE.md"
            docs.write_text(
                DOCUMENTATION.replace("Uploaded artifact.", ""), encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("docs must document sections: Evidence", result.stderr)

    def test_unevidenced_consumer_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, entry = write_fixture(root)
            entry["consumers"] = ["owner/unproven"]
            write_catalog(root, entry)
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("consumer has no validation evidence: owner/unproven", result.stderr)

    def test_beta_without_consumers_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, entry = write_fixture(root)
            entry["status"] = "beta"
            entry["consumers"] = []
            write_catalog(root, entry)
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("beta requires at least one consumer", result.stderr)


if __name__ == "__main__":
    unittest.main()
