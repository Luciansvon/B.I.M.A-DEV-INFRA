import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "dashboard.py"
SPEC = importlib.util.spec_from_file_location("dashboard", SCRIPT)
dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dashboard)


def catalog_entry(identifier, summary="Example workflow."):
    return {
        "id": identifier,
        "path": f".github/workflows/{identifier}.yml",
        "status": "experimental",
        "docs": f"docs/standards/{identifier.upper()}.md",
        "consumers": ["owner/repo"],
        "sha256": "a" * 64,
        "summary": summary,
    }


def write_inputs(root, runs, workflows=("alpha.yml", "beta.yml")):
    catalog = root / "catalog.json"
    catalog.write_text(
        json.dumps({"schema_version": 1,
                    "workflows": [catalog_entry("alpha"), catalog_entry("beta")]}),
        encoding="utf-8")
    workflows_dir = root / "workflows"
    workflows_dir.mkdir(exist_ok=True)
    for name in workflows:
        (workflows_dir / name).write_text("name: Sample\non: push\n", encoding="utf-8")
    runs_path = root / "runs.json"
    runs_path.write_text(json.dumps(runs), encoding="utf-8")
    return catalog, workflows_dir, runs_path


def run(catalog, workflows_dir, runs, output):
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT),
         "--catalog", str(catalog),
         "--workflows-dir", str(workflows_dir),
         "--runs", str(runs),
         "--output-dir", str(output)],
        cwd=ROOT, capture_output=True, text=True)


def runs_document(workflows):
    return {
        "schema_version": 1,
        "repository": "owner/repo",
        "branch": "main",
        "generated_at": "2026-10-28T00:00:00Z",
        "workflows": workflows,
    }


def run_record(conclusion="success", status="completed"):
    return {
        "status": status,
        "conclusion": conclusion,
        "created_at": "2026-10-27T00:00:00Z",
        "url": "https://github.com/owner/repo/actions/runs/1",
    }


class DashboardTests(unittest.TestCase):
    def test_workflow_without_a_run_is_rendered_as_no_direct_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runs = runs_document({"alpha.yml": run_record()})
            catalog, workflows_dir, runs_path = write_inputs(root, runs)
            result = run(catalog, workflows_dir, runs_path, root / "out")
            self.assertEqual(result.returncode, 0, result.stderr)
            page = (root / "out" / "index.html").read_text(encoding="utf-8")
            self.assertIn("no direct runs", page)
            self.assertIn("badge success", page)
            self.assertIn("Reusable workflow catalog", page)
            self.assertIn("https://github.com/owner/repo/blob/main/docs/standards/ALPHA.md", page)
            self.assertIn("missing=1", result.stdout)
            self.assertEqual(
                json.loads((root / "out" / "status.json").read_text(encoding="utf-8")),
                runs)
            self.assertNotIn("<script", page)

    def test_summary_is_escaped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = root / "catalog.json"
            catalog.write_text(json.dumps({"schema_version": 1, "workflows": [
                catalog_entry("alpha", "<script>alert(1)</script>")]}), encoding="utf-8")
            workflows_dir = root / "workflows"
            workflows_dir.mkdir()
            (workflows_dir / "alpha.yml").write_text("name: A\non: push\n", encoding="utf-8")
            runs_path = root / "runs.json"
            runs_path.write_text(json.dumps(runs_document({})), encoding="utf-8")
            result = run(catalog, workflows_dir, runs_path, root / "out")
            self.assertEqual(result.returncode, 0, result.stderr)
            page = (root / "out" / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("<script>", page)
            self.assertIn("&lt;script&gt;", page)

    def test_unknown_workflow_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runs = runs_document({"gamma.yml": run_record()})
            catalog, workflows_dir, runs_path = write_inputs(root, runs)
            result = run(catalog, workflows_dir, runs_path, root / "out")
            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown workflow file", result.stderr)
            self.assertFalse((root / "out" / "index.html").exists())

    def test_non_yaml_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runs = runs_document({})
            catalog, workflows_dir, runs_path = write_inputs(root, runs)
            (workflows_dir / "notes.txt").write_text("ignore me\n", encoding="utf-8")
            result = run(catalog, workflows_dir, runs_path, root / "out")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("workflows=2", result.stdout)

    def test_unregistered_workflow_is_not_a_failure(self):
        self.assertTrue(dashboard.missing_workflow(
            "HTTP 404: workflow dashboard.yml not found on the default branch "
            "(https://api.github.com/repos/owner/repo/actions/workflows/dashboard.yml)\n"))
        self.assertFalse(dashboard.missing_workflow(
            "HTTP 403: Resource not accessible by integration\n"))
        self.assertFalse(dashboard.missing_workflow("error connecting to api.github.com\n"))

    def test_missing_input_mode_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog, workflows_dir, _ = write_inputs(root, runs_document({}))
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT),
                 "--catalog", str(catalog),
                 "--workflows-dir", str(workflows_dir),
                 "--output-dir", str(root / "out")],
                cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("pass --runs or --fetch", result.stderr)


if __name__ == "__main__":
    unittest.main()
