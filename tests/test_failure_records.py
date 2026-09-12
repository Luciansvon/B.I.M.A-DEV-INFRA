import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation/failure_records.py"
FIXTURE = ROOT / "tests/fixtures/failure-records/records.json"
SPEC = importlib.util.spec_from_file_location("failure_records", SCRIPT)
records_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(records_module)


class FailureRecordTests(unittest.TestCase):
    def setUp(self):
        self.records = records_module.load_document(FIXTURE)

    def test_fixture_is_valid_and_summary_separates_synthetic_cases(self):
        records_module.validate_record_set(self.records)
        summary = records_module.summarize(self.records)
        self.assertEqual(summary["total_records"], 2)
        self.assertEqual(summary["real_verified_records"], 0)
        self.assertEqual(summary["synthetic_records"], 2)
        self.assertEqual(summary["active_records"], 1)

    def test_global_repeated_cause_requires_two_repositories(self):
        records = copy.deepcopy(self.records)
        records["records"][1]["scope"]["repositories"] = ["example/fixture-a"]
        with self.assertRaises(records_module.FailureRecordError):
            records_module.validate_record_set(records)

    def test_project_scope_cannot_promote_itself_global(self):
        records = copy.deepcopy(self.records)
        records["records"][0]["scope"]["promotion_basis"] = "shared_infrastructure"
        with self.assertRaises(records_module.FailureRecordError):
            records_module.validate_record_set(records)

    def test_lifecycle_invalidation_and_supersession_are_enforced(self):
        records = copy.deepcopy(self.records)
        records["records"][0]["status"] = "INVALIDATED"
        with self.assertRaises(records_module.FailureRecordError):
            records_module.validate_record_set(records)
        records = copy.deepcopy(self.records)
        records["records"][0]["status"] = "SUPERSEDED"
        with self.assertRaises(records_module.FailureRecordError):
            records_module.validate_record_set(records)
        records = copy.deepcopy(self.records)
        records["records"][0]["supersedes"] = ["fixture-invalidated"]
        with self.assertRaises(records_module.FailureRecordError):
            records_module.validate_record_set(records)

    def test_review_and_verification_evidence_are_mandatory(self):
        for field, container in (
                ("reviewed_by", "review"),
                ("evidence_refs", "cause"),
                ("verification_refs", "fix")):
            records = copy.deepcopy(self.records)
            records["records"][0][container][field] = [] if field.endswith("refs") else ""
            with self.subTest(field=field), self.assertRaises(records_module.FailureRecordError):
                records_module.validate_record_set(records)
        records = copy.deepcopy(self.records)
        records["records"][0]["review"]["reviewed_by"] = "fixture-owner"
        with self.assertRaises(records_module.FailureRecordError):
            records_module.validate_record_set(records)

    def test_unknown_duplicate_nonfinite_and_unsorted_records_fail_closed(self):
        with self.assertRaises(records_module.FailureRecordError):
            records_module.strict_json(b'{"schema":"x","schema":"y"}')
        with self.assertRaises(records_module.FailureRecordError):
            records_module.strict_json(b'{"number":NaN}')
        records = copy.deepcopy(self.records)
        records["records"][0]["unknown"] = True
        with self.assertRaises(records_module.FailureRecordError):
            records_module.validate_record_set(records)
        records = copy.deepcopy(self.records)
        records["records"].reverse()
        with self.assertRaises(records_module.FailureRecordError):
            records_module.validate_record_set(records)

    def test_cli_exports_canonical_records_and_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            run = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), "--input", str(FIXTURE),
                 "--output", str(output)],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            exported = (output / "records.json").read_bytes()
            self.assertEqual(exported, records_module.canonical_bytes(self.records))
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["real_verified_records"], 0)


if __name__ == "__main__":
    unittest.main()
