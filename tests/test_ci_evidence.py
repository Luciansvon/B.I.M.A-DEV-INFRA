import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_SCRIPT = ROOT / "automation" / "write_ci_summary.py"
COMPARE_SCRIPT = ROOT / "automation" / "compare_audit_evidence.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


summary = load("write_ci_summary", SUMMARY_SCRIPT)
compare = load("compare_audit_evidence", COMPARE_SCRIPT)


class CiEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_summary_passes_only_when_every_component_passes(self):
        for relative in summary.COMPONENTS.values():
            (self.root / relative).write_text("0\n", encoding="utf-8")
        result = summary.create_summary(self.root)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(all(item["status"] == "pass" for item in result["components"].values()))

        (self.root / "tests.exit-code").write_text("1\n", encoding="utf-8")
        self.assertEqual(summary.create_summary(self.root)["status"], "fail")
        (self.root / "tests.exit-code").unlink()
        self.assertEqual(summary.create_summary(self.root)["status"], "error")

    def test_comparison_excludes_generated_timestamp(self):
        baseline = {field: None for field in compare.FIELDS}
        baseline.update({"schema_version": 1, "module": "repository-audit", "status": "pass"})
        left = {**baseline, "generated_at": "first"}
        right = {**baseline, "generated_at": "second"}
        self.assertEqual(compare.comparable(left), compare.comparable(right))

    def test_comparison_cli_reports_differences(self):
        left = self.root / "left.json"
        right = self.root / "right.json"
        output = self.root / "comparison.json"
        left.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
        right.write_text(json.dumps({"status": "fail"}), encoding="utf-8")
        run = subprocess.run(
            [sys.executable, "-I", str(COMPARE_SCRIPT), str(left), str(right), "--output", str(output)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(run.returncode, 1)
        result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "fail")
        self.assertIn("status", result["differences"])


if __name__ == "__main__":
    unittest.main()
