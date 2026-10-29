import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
PROOF = ROOT / ".github" / "workflows" / "trusted-launcher-proof.yml"
JOB = "trusted-repository-audit-self-call"
JOB_HEADER = re.compile(r"^  [A-Za-z0-9_-]+:\s*$", re.MULTILINE)
FALSE_CONDITION = re.compile(
    r"^\s*if:\s*(false|\$\{\{\s*false\s*\}\})\s*$", re.MULTILINE)
PIN = re.compile(
    r"Luciansvon/B\.I\.M\.A-DEV-INFRA/\.github/workflows/"
    r"trusted-repository-audit\.yml@([0-9a-f]{40}) # v1")


def job_block(text, name):
    header = re.search(rf"^  {re.escape(name)}:\s*$", text, re.MULTILINE)
    if header is None:
        return None
    following = JOB_HEADER.search(text, header.end())
    return text[header.end():following.start() if following else len(text)]


class CiWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")
        self.block = job_block(self.text, JOB)
        self.assertIsNotNone(self.block, f"missing CI job: {JOB}")

    def test_job_calls_the_pinned_trusted_workflow(self):
        self.assertIn("name: Trusted repository audit self-call", self.block)
        uses = [line for line in self.block.splitlines() if "uses:" in line]
        self.assertEqual(len(uses), 1, uses)
        pin = PIN.search(uses[0])
        self.assertIsNotNone(pin, uses[0])
        self.assertIn(pin.group(1), PROOF.read_text(encoding="utf-8"))

    def test_permissions_are_read_only(self):
        self.assertIn("permissions:\n      contents: read", self.block)
        self.assertNotIn("contents: write", self.block)
        self.assertNotIn("id-token:", self.block)
        self.assertNotIn("security-events:", self.block)

    def test_artifact_name_is_set(self):
        self.assertIn("with:\n      artifact-name: trusted-self-audit", self.block)

    def test_no_secrets_pull_request_target_or_continue_on_error(self):
        self.assertNotIn("secrets:", self.block)
        self.assertNotIn("secrets: inherit", self.block)
        self.assertNotIn("continue-on-error", self.block)
        self.assertNotIn("pull_request_target", self.text)

    def test_job_is_not_skipped_by_a_false_condition(self):
        self.assertNotIn("if: false", self.block)
        self.assertIsNone(FALSE_CONDITION.search(self.block))


if __name__ == "__main__":
    unittest.main()
