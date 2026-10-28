import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
SELF_TEST = ROOT / ".github" / "workflows" / "release-template-self-test.yml"
REMOTE_USES = re.compile(r"^\s*uses:\s*(\S+)(?:\s+#.*)?$", re.MULTILINE)
SHA_PIN = re.compile(r"@[0-9a-f]{40}$")


class ReleaseWorkflowTests(unittest.TestCase):
    def test_publication_is_a_pinned_reusable_workflow(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("on:\n  workflow_call:", text)
        self.assertIn("runs-on: ubuntu-24.04", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("timeout-minutes: 15", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("contents: write", text)
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("secrets: inherit", text)
        remote = [item for item in REMOTE_USES.findall(text)
                  if not item.startswith(("./", "$/"))]
        self.assertTrue(remote)
        for reference in remote:
            with self.subTest(reference=reference):
                self.assertRegex(reference, SHA_PIN)

    def test_tag_and_asset_policy_fails_closed(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            r"^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z][0-9A-Za-z.-]*)?$", text)
        self.assertIn(r"^[0-9a-f]{40}$", text)
        self.assertIn("already exists; release tags are not overwritten", text)
        self.assertIn("could not verify tag status", text)
        self.assertIn("selected no release assets", text)
        self.assertIn("duplicate release asset name", text)
        self.assertIn("empty release asset", text)
        self.assertIn("regular file inside the caller checkout", text)

    def test_dry_run_never_writes_and_real_run_is_draft_first(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('if [[ "$DRY_RUN" == "true" ]]', text)
        self.assertIn("--draft", text)
        self.assertIn("--draft=false", text)
        self.assertIn('[[ "$PRERELEASE" == "true" ]] && create_args+=(--prerelease)', text)
        self.assertIn("if-no-files-found: warn", text)
        self.assertIn("release.json", text)

    def test_self_test_calls_the_template_with_dry_run(self):
        text = SELF_TEST.read_text(encoding="utf-8")
        self.assertIn("uses: ./.github/workflows/release.yml # zizmor: ignore[self-repository]", text)
        self.assertIn("dry-run: true", text)
        self.assertIn("tag: v0.0.0-self-test", text)
        self.assertIn("target-sha: ${{ github.sha }}", text)
        self.assertIn("contents: write", text)
        self.assertNotIn("pull_request:", text)


if __name__ == "__main__":
    unittest.main()
