import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "fleet_dispatch.py"


def fleet(repositories=None):
    return {
        "schema": "bima-fleet.v1",
        "schema_version": 1,
        "repositories": repositories if repositories is not None else [
            {"repository": "owner/one",
             "workflow": ".github/workflows/bima-shared-audit.yml"},
            {"repository": "owner/two",
             "workflow": ".github/workflows/repository-audit.yml"},
        ],
    }


def run(document, output, ref="main", apply=False):
    with tempfile.TemporaryDirectory() as temporary:
        fleet_path = Path(temporary) / "repos.json"
        fleet_path.write_text(json.dumps(document), encoding="utf-8")
        arguments = [sys.executable, "-I", str(SCRIPT),
                     "--fleet", str(fleet_path), f"--ref={ref}",
                     "--output", str(output)]
        if apply:
            arguments.append("--apply")
        return subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True)


class FleetDispatchTests(unittest.TestCase):
    def test_repository_fleet_plans_every_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            result = run(fleet(), output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("mode=dry-run", result.stdout)
            self.assertIn("repositories=2", result.stdout)
            evidence = json.loads(
                (output / "evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(evidence["mode"], "dry-run")
            self.assertEqual(evidence["ref"], "main")
            self.assertEqual([item["repository"] for item in evidence["dispatches"]],
                             ["owner/one", "owner/two"])
            for item in evidence["dispatches"]:
                self.assertEqual(item["status"], "planned")
                self.assertIsNone(item["run_id"])
                self.assertIsNone(item["run_url"])

    def test_duplicate_repository_fails_without_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            result = run(fleet([
                {"repository": "owner/one",
                 "workflow": ".github/workflows/bima-shared-audit.yml"},
                {"repository": "owner/ONE",
                 "workflow": ".github/workflows/bima-shared-audit.yml"},
            ]), output)
            self.assertEqual(result.returncode, 2)
            self.assertIn("duplicate repository", result.stderr)
            self.assertFalse((output / "evidence.json").exists())

    def test_unknown_entry_field_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            result = run(fleet([{
                "repository": "owner/one",
                "workflow": ".github/workflows/bima-shared-audit.yml",
                "ref": "main",
            }]), output)
            self.assertEqual(result.returncode, 2)
            self.assertIn("keys must be exactly", result.stderr)

    def test_workflow_must_live_in_the_workflows_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            result = run(fleet([{
                "repository": "owner/one",
                "workflow": "../../etc/passwd",
            }]), output)
            self.assertEqual(result.returncode, 2)
            self.assertIn(".github/workflows", result.stderr)

    def test_empty_fleet_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            result = run(fleet([]), output)
            self.assertEqual(result.returncode, 2)
            self.assertIn("1-30 entries", result.stderr)

    def test_strict_json_rejects_duplicates_and_nonfinite_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fleet_path = root / "repos.json"
            output = root / "evidence"
            cases = [
                ('{"schema": "bima-fleet.v1", "schema_version": 1,'
                 ' "repositories": [], "repositories": []}', "duplicate key"),
                ('{"schema": "bima-fleet.v1", "schema_version": NaN,'
                 ' "repositories": []}', "non-finite number"),
            ]
            for raw, message in cases:
                with self.subTest(message=message):
                    fleet_path.write_text(raw, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-I", str(SCRIPT),
                         "--fleet", str(fleet_path), "--output", str(output)],
                        cwd=ROOT, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn(message, result.stderr)
            self.assertFalse((output / "evidence.json").exists())

    def test_ref_cannot_escape_the_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            for ref in ["../main", "-main", "main/", "main//x"]:
                result = run(fleet(), output, ref=ref)
                self.assertEqual(result.returncode, 2, ref)
                self.assertIn("ref must be", result.stderr)
            self.assertFalse((output / "evidence.json").exists())


if __name__ == "__main__":
    unittest.main()
