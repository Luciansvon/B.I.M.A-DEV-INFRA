import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "roadmap_audit.py"
TODAY = "2026-10-28"
HEADER = ("| id | why | state | gate | precursor | verify | evidence | done when | review-by |\n"
          "|---|---|---|---|---|---|---|---|---|\n")


def run(root, *args):
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--root", str(root), "--today", TODAY, *args],
        cwd=ROOT, capture_output=True, text=True)


def fixture(temporary, actionable="", gated="", done=""):
    root = Path(temporary)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "NEXT.md").write_text(
        "# Next\n\n## Lane 1 — Actionable now\n\n"
        + HEADER + actionable + "\n## Lane 2 — Gated\n\n"
        + HEADER + gated + "\n## Done — last 90 days\n\n"
        + HEADER + done, encoding="utf-8")
    (root / "Taskfile.yml").write_text(
        "version: '3'\n\ntasks:\n  test:\n    cmds:\n      - echo test\n"
        "  coverage:\n    cmds:\n      - echo coverage\n", encoding="utf-8")
    (root / ".bima").mkdir(parents=True, exist_ok=True)
    (root / ".bima" / "audit.json").write_text(
        json.dumps({"required_files": []}), encoding="utf-8")
    (root / "automation").mkdir(parents=True, exist_ok=True)
    (root / "automation" / "sample.py").write_text("pass\n", encoding="utf-8")
    (root / "docs" / "audits").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "audits" / "VALIDATION-2026-10-28-SAMPLE.md").write_text(
        "# Sample validation\n", encoding="utf-8")
    return root


def row(identifier, state="actionable", gate="-", precursor="-",
        verify="task test", evidence="-", review="2026-11-20"):
    return (f"| {identifier} | Local work | {state} | {gate} | {precursor} | "
            f"{verify} | {evidence} | The check passes | {review} |\n")


class RoadmapAuditTests(unittest.TestCase):
    def test_valid_fixture_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = fixture(temporary, actionable=row("P4-01"))
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("actionable=1", result.stdout)

    def test_empty_actionable_lane_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = fixture(temporary)
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Lane 1 is empty", result.stderr)

    def test_blocked_without_precursor_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = fixture(temporary, actionable=row("P4-01"), gated=row(
                "P4-02", state="blocked", gate="consumer: real repository",
                precursor="-"))
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("needs an existing precursor", result.stderr)

    def test_expired_review_date_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = fixture(temporary, actionable=row("P4-01", review="2026-10-01"))
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("has expired", result.stderr)

    def test_done_without_evidence_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = fixture(temporary, actionable=row("P4-01"),
                           done=row("P4-00", state="done"))
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("needs committed evidence", result.stderr)

    def test_done_evidence_must_mention_the_item_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = fixture(
                temporary, actionable=row("P4-01"),
                done=row("P4-00", state="done",
                         evidence="docs/audits/VALIDATION-2026-10-28-SAMPLE.md"))
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("evidence does not mention P4-00", result.stderr)

    def test_unknown_verify_task_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = fixture(temporary, actionable=row("P4-01", verify="task missing"))
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown Taskfile task", result.stderr)

    def test_candidates_detect_unprotected_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = fixture(temporary, actionable=row("P4-01"))
            result = run(root, "--candidates")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("candidate: required-file automation/sample.py", result.stdout)


if __name__ == "__main__":
    unittest.main()
