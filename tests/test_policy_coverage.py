import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "policy_coverage.py"


def run(root):
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--root", str(root)],
        cwd=ROOT, capture_output=True, text=True)


def write_fixture(root):
    files = {
        "automation/sample.py": "",
        "automation/sample.sh": "#!/bin/sh\n",
        "schemas/sample.schema.json": "{}\n",
        ".github/workflows/sample.yml": "name: Sample\n",
        "docs/standards/SAMPLE.md": "# Sample\n",
        "docs/architecture/ARCH.md": "# Architecture\n",
        "docs/decisions/ADR-0001.md": "# ADR\n",
        "docs/incidents/INCIDENTS.md": "# Incidents\n",
        "docs/NEXT.md": "# Next\n",
    }
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    catalog = root / "catalog" / "workflows.json"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(json.dumps({
        "schema": "bima-workflow-catalog.v1",
        "schema_version": 1,
        "workflows": [{"path": ".github/workflows/sample.yml",
                       "docs": "docs/standards/SAMPLE.md"}],
    }, indent=2) + "\n", encoding="utf-8")
    return write_policy(root, sorted(files))


def write_policy(root, required):
    policy = root / ".bima" / "audit.json"
    policy.parent.mkdir(parents=True, exist_ok=True)
    policy.write_text(json.dumps({
        "schema_version": 1,
        "required_files": required,
        "max_file_bytes": 1048576,
    }, indent=2) + "\n", encoding="utf-8")
    return policy


class PolicyCoverageTests(unittest.TestCase):
    def test_valid_fixture_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            write_fixture(Path(temporary))
            result = run(temporary)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("policy-coverage: pass; required=9; covered=9", result.stdout)

    def test_unprotected_automation_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            (root / "automation" / "extra.py").write_text("", encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("automation/extra.py", result.stderr)

    def test_unprotected_catalog_path_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            catalog = root / "catalog" / "workflows.json"
            document = json.loads(catalog.read_text(encoding="utf-8"))
            document["workflows"].append({"path": ".github/workflows/extra.yml",
                                          "docs": "docs/standards/SAMPLE.md"})
            catalog.write_text(json.dumps(document), encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn(".github/workflows/extra.yml", result.stderr)

    def test_missing_required_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            write_policy(root, ["automation/sample.py", "automation/sample.sh",
                                "schemas/sample.schema.json",
                                ".github/workflows/sample.yml",
                                "docs/standards/SAMPLE.md",
                                "docs/architecture/ARCH.md",
                                "docs/decisions/ADR-0001.md",
                                "docs/incidents/INCIDENTS.md",
                                "docs/NEXT.md",
                                "automation/gone.py"])
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("required file is missing: automation/gone.py", result.stderr)

    def test_deleted_decision_or_incident_fails_the_policy_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            (root / "docs/decisions/ADR-0001.md").unlink()
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn(
                "required file is missing: docs/decisions/ADR-0001.md", result.stderr)

    def test_new_decision_without_a_required_entry_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            (root / "docs/decisions/ADR-0002.md").write_text(
                "# ADR 2\n", encoding="utf-8")
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn(
                "not protected by required_files: docs/decisions/ADR-0002.md",
                result.stderr)

    def test_duplicate_required_entry_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root)
            write_policy(root, ["automation/sample.py", "automation/sample.sh",
                                "schemas/sample.schema.json",
                                ".github/workflows/sample.yml",
                                "docs/standards/SAMPLE.md",
                                "docs/architecture/ARCH.md",
                                "docs/decisions/ADR-0001.md",
                                "docs/incidents/INCIDENTS.md",
                                "docs/NEXT.md",
                                "docs/NEXT.md"])
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("duplicate required entry: docs/NEXT.md", result.stderr)


if __name__ == "__main__":
    unittest.main()
