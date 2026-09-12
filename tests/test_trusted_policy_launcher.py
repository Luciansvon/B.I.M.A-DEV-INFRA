import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_RELATIVE = Path("automation/trusted_policy_launcher.py")
BUNDLE_ID = "dev-infra-repository-audit.v1"


class TrustedPolicyLauncherTests(unittest.TestCase):
    def git(self, root, *args):
        return subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True,
            text=True, timeout=30).stdout.strip()

    def copy_checkout(self, destination):
        shutil.copytree(
            ROOT, destination,
            ignore=shutil.ignore_patterns(".git", ".artifacts", ".tools", "__pycache__", "*.pyc"),
        )
        self.git(destination, "init", "-q")
        self.git(destination, "config", "user.name", "Test")
        self.git(destination, "config", "user.email", "test@example.invalid")
        self.git(destination, "config", "commit.gpgsign", "false")
        self.git(destination, "add", ".")
        self.git(destination, "commit", "-qm", "fixture")
        return self.git(destination, "rev-parse", "HEAD")

    def fixture(self, temporary):
        temporary = Path(temporary)
        infra = temporary / "infra"
        subject = temporary / "subject"
        infra_revision = self.copy_checkout(infra)
        self.copy_checkout(subject)
        evidence = temporary / "evidence" / "decision.json"
        return infra, subject, infra_revision, evidence

    def environment(self, infra_revision, **replacements):
        values = {
            "BIMA_TRUSTED_ACTOR": "test-runner",
            "BIMA_SUBJECT_REPOSITORY": "Luciansvon/B.I.M.A-DEV-INFRA",
            "BIMA_WORKFLOW_REPOSITORY": "Luciansvon/B.I.M.A-DEV-INFRA",
            "BIMA_WORKFLOW_REF": (
                "Luciansvon/B.I.M.A-DEV-INFRA/"
                f".github/workflows/trusted-repository-audit.yml@{infra_revision}"
            ),
            "BIMA_WORKFLOW_SHA": infra_revision,
            "BIMA_RUN_ID": "123456",
            "BIMA_RUN_ATTEMPT": "1",
        }
        values.update(replacements)
        return {**os.environ, **values}

    def run_launcher(self, infra, subject, evidence, environment, *extra):
        return subprocess.run(
            [
                sys.executable, "-I", str(infra / LAUNCHER_RELATIVE),
                "--infra-root", str(infra),
                "--subject-root", str(subject),
                "--bundle-id", BUNDLE_ID,
                "--project-path", ".bima/project.json",
                "--evidence-output", str(evidence),
                *extra,
            ],
            env=environment, capture_output=True, text=True, timeout=60,
        )

    def load_evidence(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_pinned_separate_checkouts_allow_reviewed_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra, subject, revision, evidence = self.fixture(temporary)
            run = self.run_launcher(
                infra, subject, evidence, self.environment(revision))
            self.assertEqual(run.returncode, 0, run.stderr)
            decision = self.load_evidence(evidence)
            self.assertEqual(decision["decision"], "ALLOW")
            self.assertTrue(decision["verifier_launched"])
            self.assertTrue((subject / ".artifacts/policy-gate/audit/result.json").is_file())

    def test_subject_policy_shadow_cannot_change_trusted_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra, subject, revision, evidence = self.fixture(temporary)
            policy_path = subject / "policies/repository-audit/dev-infra.v1.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["operations"][0]["network_destinations"] = ["attacker.invalid"]
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            self.git(subject, "add", ".")
            self.git(subject, "commit", "-qm", "subject policy attack")
            run = self.run_launcher(
                infra, subject, evidence, self.environment(revision))
            self.assertEqual(run.returncode, 0, run.stderr)
            decision = self.load_evidence(evidence)
            self.assertEqual(decision["decision"], "ALLOW")
            self.assertEqual(
                decision["policy_sha256"],
                "49075f4408d07a0d9a4d12db43f14dcc72e5795e1cd75fde729294b74a085161",
            )

    def test_project_scope_elevation_is_denied_without_verifier(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra, subject, revision, evidence = self.fixture(temporary)
            project_path = subject / ".bima/project.json"
            project = json.loads(project_path.read_text(encoding="utf-8"))
            project["operations"][0]["output_root"] = ".artifacts/attacker"
            project_path.write_text(json.dumps(project), encoding="utf-8")
            self.git(subject, "add", ".")
            self.git(subject, "commit", "-qm", "scope elevation attack")
            run = self.run_launcher(
                infra, subject, evidence, self.environment(revision))
            self.assertEqual(run.returncode, 3, run.stderr)
            decision = self.load_evidence(evidence)
            self.assertEqual(decision["decision"], "DENY")
            self.assertEqual(decision["reason_code"], "OUTPUT_SCOPE_DENIED")
            self.assertFalse(decision["verifier_launched"])
            self.assertFalse((subject / ".artifacts/attacker/audit").exists())

    def test_workflow_ref_mismatch_is_denied_before_verifier(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra, subject, revision, evidence = self.fixture(temporary)
            environment = self.environment(
                revision,
                BIMA_WORKFLOW_REF=(
                    "Luciansvon/B.I.M.A-DEV-INFRA/"
                    ".github/workflows/trusted-repository-audit.yml@" + "0" * 40
                ),
            )
            run = self.run_launcher(infra, subject, evidence, environment)
            self.assertEqual(run.returncode, 3, run.stderr)
            decision = self.load_evidence(evidence)
            self.assertEqual(decision["reason_code"], "WORKFLOW_REF_MISMATCH")
            self.assertFalse(decision["verifier_launched"])
            self.assertFalse((subject / ".artifacts/policy-gate/audit").exists())

    def test_reusable_workflow_does_not_delegate_bundle_selection(self):
        workflow = (ROOT / ".github/workflows/trusted-repository-audit.yml").read_text(
            encoding="utf-8")
        bundle = json.loads(
            (ROOT / "policies/trust-bundles/dev-infra-repository-audit.v1.json")
            .read_text(encoding="utf-8"))
        self.assertNotIn("trust-bundle-id:", workflow)
        self.assertIn(f"BIMA_TRUST_BUNDLE_ID: {bundle['bundle_id']}", workflow)

    def test_committed_policy_tamper_fails_bundle_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra, subject, _, evidence = self.fixture(temporary)
            policy_path = infra / "policies/repository-audit/dev-infra.v1.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["budget"]["max_calls"] = 2
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            self.git(infra, "add", ".")
            self.git(infra, "commit", "-qm", "tampered reviewed policy")
            tampered_revision = self.git(infra, "rev-parse", "HEAD")
            run = self.run_launcher(
                infra, subject, evidence, self.environment(tampered_revision))
            self.assertEqual(run.returncode, 3, run.stderr)
            decision = self.load_evidence(evidence)
            self.assertEqual(decision["reason_code"], "TRUSTED_POLICY_HASH_MISMATCH")
            self.assertFalse(decision["verifier_launched"])

    def test_overlap_and_subject_repository_spoof_are_denied(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra, subject, revision, evidence = self.fixture(temporary)
            overlap = self.run_launcher(
                infra, infra, evidence, self.environment(revision))
            self.assertEqual(overlap.returncode, 3, overlap.stderr)
            self.assertEqual(
                self.load_evidence(evidence)["reason_code"], "CHECKOUTS_NOT_SEPARATE")

            evidence.unlink()
            spoofed = self.run_launcher(
                infra, subject, evidence,
                self.environment(revision, BIMA_SUBJECT_REPOSITORY="attacker/repo"),
            )
            self.assertEqual(spoofed.returncode, 3, spoofed.stderr)
            self.assertEqual(
                self.load_evidence(evidence)["reason_code"], "SUBJECT_REPOSITORY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
