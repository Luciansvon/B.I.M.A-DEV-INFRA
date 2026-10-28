import re
import shutil
import subprocess
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "security-supply-chain.yml"
CI = ROOT / ".github" / "workflows" / "ci.yml"
INSTALLER = ROOT / "automation" / "install_security_tools.sh"
REMOTE_USES = re.compile(r"^\s*uses:\s*(\S+)(?:\s+#.*)?$", re.MULTILINE)
SHA_PIN = re.compile(r"@[0-9a-f]{40}$")
DIGESTS = {
    "9f42f94fca5b8d04c13bccfbb331104b37a9250650d89ae58dc888d46206f9b9",
    "d1cffebe5704b74e2e5f8a864efb9f7e54768972dc686188c008033fb1797841",
    "d185f726bdaf92df78273217dfdd24ebcd6b0ef48cf3ce776ff5762b6e138c99",
}


class SecuritySupplyChainTests(unittest.TestCase):
    def test_reusable_workflow_is_pinned_and_minimal(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("on:\n  workflow_call:", text)
        self.assertIn("runs-on: ubuntu-24.04", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("job.workflow_repository", text)
        self.assertIn("job.workflow_sha", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn(
            "if: ${{ inputs.dependency-review && github.event_name == 'pull_request' }}",
            text)
        self.assertIn(
            "actions/dependency-review-action@"
            "a1d282b36b6f3519aa1f3fc636f609c47dddb294 # v5.0.0", text)
        self.assertIn("fail-on-severity: high", text)
        self.assertIn("comment-summary-in-pr: never", text)
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("secrets: inherit", text)
        self.assertNotIn("--fix=true", text)
        self.assertIn("--fix=false --no-api", text)
        self.assertIn("--offline --strict-collection", text)
        remote = [item for item in REMOTE_USES.findall(text)
                  if not item.startswith(("./", "$/"))]
        self.assertTrue(remote)
        for reference in remote:
            with self.subTest(reference=reference):
                self.assertRegex(reference, SHA_PIN)

    def test_installer_verifies_every_download(self):
        text = INSTALLER.read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", text)
        self.assertIn("sha256sum --check --status", text)
        self.assertIn("action-validator_linux_amd64", text)
        self.assertIn("pinact_linux_amd64.tar.gz", text)
        self.assertIn("zizmor-x86_64-unknown-linux-gnu.tar.gz", text)
        for digest in DIGESTS:
            self.assertIn(digest, text)
        self.assertIn("for tool in action-validator pinact zizmor; do", text)
        self.assertIn('[[ -x "$destination/$tool" ]]', text)
        bash = shutil.which("bash")
        if bash and sys.platform != "win32":
            subprocess.run([bash, "-n", str(INSTALLER)], check=True)

    def test_ci_uses_the_shared_installer_and_self_test(self):
        text = CI.read_text(encoding="utf-8")
        self.assertIn(
            "uses: ./.github/workflows/security-supply-chain.yml "
            "# zizmor: ignore[self-repository]", text)
        self.assertIn("dependency-review: false", text)
        self.assertIn(
            "bash automation/install_security_tools.sh", text)
        self.assertEqual(text.count("bima-security-tools"), 2)


if __name__ == "__main__":
    unittest.main()
