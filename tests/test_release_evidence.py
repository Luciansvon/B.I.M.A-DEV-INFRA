import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation/release_evidence.py"
FIXTURES = ROOT / "tests/fixtures/release"
SPEC = importlib.util.spec_from_file_location("release_evidence", SCRIPT)
evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence)


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ReleaseEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.document = load("evidence-dry-run.json")

    def assert_rejected(self, value):
        with self.assertRaises(evidence.ReleaseEvidenceError):
            evidence.validate_evidence(value)

    def test_dry_run_evidence_written_by_the_workflow_is_valid(self):
        validated = evidence.validate_evidence(copy.deepcopy(self.document))
        self.assertEqual(len(validated["assets"]), 2)
        self.assertTrue(validated["dry_run"])
        self.assertIsNone(validated["release_url"])

    def test_negative_fixtures_fail_closed(self):
        for name in (
            "evidence-missing-field.json",
            "evidence-duplicate-asset.json",
            "evidence-bad-digest.json",
            "evidence-zero-size.json",
        ):
            with self.subTest(fixture=name):
                self.assert_rejected(load(name))

    def test_unknown_top_level_and_asset_fields_fail_closed(self):
        unknown = copy.deepcopy(self.document)
        unknown["notes"] = "not in the contract"
        self.assert_rejected(unknown)
        unknown = copy.deepcopy(self.document)
        unknown["assets"][0]["url"] = "https://example.invalid/asset"
        self.assert_rejected(unknown)

    def test_tag_types_and_url_rules_fail_closed(self):
        cases = []
        value = copy.deepcopy(self.document)
        value["tag"] = "1.2.3"
        cases.append(value)
        value = copy.deepcopy(self.document)
        value["published"] = "false"
        cases.append(value)
        value = copy.deepcopy(self.document)
        value["run_url"] = ""
        cases.append(value)
        value = copy.deepcopy(self.document)
        value["dry_run"] = False
        value["published"] = True
        cases.append(value)
        value = copy.deepcopy(self.document)
        value["schema_version"] = True
        cases.append(value)
        for value in cases:
            with self.subTest(value=value):
                self.assert_rejected(value)

    def test_duplicate_json_keys_fail_closed(self):
        with self.assertRaises(evidence.ReleaseEvidenceError):
            evidence.strict_json(b'{"schema":"x","schema":"y"}')

    def test_cli_reports_pass_and_asset_count(self):
        run = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "validate", "--input",
             str(FIXTURES / "evidence-dry-run.json")],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "release-evidence: pass; assets=2")

    def test_cli_reports_failure_with_exit_two(self):
        run = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "validate", "--input",
             str(FIXTURES / "evidence-missing-field.json")],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertTrue(
            run.stdout.startswith("release-evidence: fail: "), run.stdout)


if __name__ == "__main__":
    unittest.main()
