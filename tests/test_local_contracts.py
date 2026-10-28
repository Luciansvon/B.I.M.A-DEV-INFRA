import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "automation" / "local_contracts.py"
SUMMARY = re.compile(r"^local-contracts: PASS; contracts=(\d+); failed=0$", re.MULTILINE)


class LocalContractsHarnessTests(unittest.TestCase):
    def test_harness_reports_one_pass_summary(self):
        run = subprocess.run(
            [sys.executable, "-I", str(HARNESS)],
            cwd=ROOT, capture_output=True, text=True, timeout=55)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        match = SUMMARY.search(run.stdout)
        self.assertIsNotNone(match, run.stdout)
        self.assertGreaterEqual(int(match.group(1)), 8)


if __name__ == "__main__":
    unittest.main()
