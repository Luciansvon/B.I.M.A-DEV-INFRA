import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "workflow_refs.py"
REPOSITORY = "Luciansvon/B.I.M.A-DEV-INFRA"


class WorkflowRefsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.git("init", "-q")
        self.put(".github/workflows/base.yml", "on:\n  workflow_call:\n")
        self.sha = self.commit("base workflow")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args], check=True, capture_output=True,
            text=True, timeout=30).stdout.strip()

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def commit(self, message):
        self.git("add", "-A")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def caller(self, uses, infra_ref=None):
        lines = ["jobs:", "  audit:", f"    uses: {uses}"]
        if infra_ref is not None:
            lines += ["    with:", f"      infra-ref: {infra_ref}"]
        return self.put(".github/workflows/caller.yml", "\n".join(lines) + "\n")

    def run_tool(self):
        return subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "--root", str(self.root)],
            capture_output=True, text=True, timeout=60)

    def test_valid_local_and_external_references_pass(self):
        self.caller(f"{REPOSITORY}/.github/workflows/base.yml@{self.sha}", self.sha)
        self.put(".github/workflows/local.yml",
                 "jobs:\n  audit:\n    uses: ./.github/workflows/base.yml\n")
        self.commit("valid callers")
        run = self.run_tool()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "workflow-refs: pass; files=3; refs=2")

    def test_infra_ref_must_match_the_workflow_ref(self):
        self.caller(
            f"{REPOSITORY}/.github/workflows/base.yml@{self.sha}", "0" * 40)
        self.commit("mismatched infra-ref")
        run = self.run_tool()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertIn("caller.yml:3: infra-ref does not match", run.stderr)

    def test_mutable_ref_is_rejected(self):
        self.caller(f"{REPOSITORY}/.github/workflows/base.yml@v1")
        self.commit("mutable ref")
        run = self.run_tool()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertIn("caller.yml:3: reusable workflow ref is not a full commit SHA",
                      run.stderr)

    def test_missing_revision_is_rejected(self):
        self.caller(f"{REPOSITORY}/.github/workflows/base.yml@{'0' * 40}")
        self.commit("missing revision")
        run = self.run_tool()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertIn("revision", run.stderr)
        self.assertIn("is not available", run.stderr)

    def test_workflow_must_exist_at_the_revision(self):
        self.caller(f"{REPOSITORY}/.github/workflows/absent.yml@{self.sha}")
        self.commit("missing workflow path")
        run = self.run_tool()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertIn("workflow is missing at revision", run.stderr)

    def test_local_reference_must_resolve(self):
        self.put(".github/workflows/local.yml",
                 "jobs:\n  audit:\n    uses: ./.github/workflows/absent.yml\n")
        self.commit("missing local workflow")
        run = self.run_tool()
        self.assertEqual(run.returncode, 2, run.stdout)
        self.assertIn("local workflow does not exist", run.stderr)


if __name__ == "__main__":
    unittest.main()
