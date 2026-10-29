import hashlib
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
        self.git(destination, "config", "gc.auto", "0")
        self.git(destination, "config", "maintenance.auto", "false")
        self.git(destination, "add", ".")
        self.git(destination, "commit", "-qm", "fixture")
        return self.git(destination, "rev-parse", "HEAD")

    def commit(self, root, message):
        self.git(root, "add", "-A")
        self.git(root, "commit", "-qm", message)
        return self.git(root, "rev-parse", "HEAD")

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

    def test_pull_request_uses_base_audit_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra, subject, revision, evidence = self.fixture(temporary)
            base = self.git(subject, "rev-parse", "HEAD")
            base_policy = (subject / ".bima/audit.json").read_bytes()
            policy = json.loads(base_policy)
            policy["max_file_bytes"] = 1
            (subject / ".bima/audit.json").write_text(json.dumps(policy), encoding="utf-8")
            head_policy = (subject / ".bima/audit.json").read_bytes()
            self.commit(subject, "weaken audit policy in the pull request")
            run = self.run_launcher(
                infra, subject, evidence,
                self.environment(
                    revision, BIMA_EVENT_NAME="pull_request", BIMA_BASE_SHA=base))
            self.assertEqual(run.returncode, 0, run.stderr)
            decision = self.load_evidence(evidence)
            self.assertEqual(decision["decision"], "ALLOW")
            result = json.loads(
                (subject / ".artifacts/policy-gate/audit/result.json")
                .read_text(encoding="utf-8"))
            self.assertEqual(
                result["policy_sha256"], hashlib.sha256(base_policy).hexdigest())
            self.assertNotEqual(
                result["policy_sha256"], hashlib.sha256(head_policy).hexdigest())

    def test_pull_request_base_policy_detects_deleted_required_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra, subject, revision, evidence = self.fixture(temporary)
            base = self.git(subject, "rev-parse", "HEAD")
            (subject / "AGENTS.md").unlink()
            self.commit(subject, "delete a required file")
            run = self.run_launcher(
                infra, subject, evidence,
                self.environment(
                    revision, BIMA_EVENT_NAME="pull_request", BIMA_BASE_SHA=base))
            self.assertEqual(run.returncode, 1, run.stderr)
            decision = self.load_evidence(evidence)
            self.assertEqual(decision["decision"], "ALLOW")
            self.assertTrue(decision["verifier_launched"])
            result = json.loads(
                (subject / ".artifacts/policy-gate/audit/result.json")
                .read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "fail")
            self.assertIn(
                "required-file", [item["code"] for item in result["findings"]])

    def test_pull_request_cannot_switch_the_audit_policy_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra, subject, revision, evidence = self.fixture(temporary)
            base = self.git(subject, "rev-parse", "HEAD")
            project_path = subject / ".bima/project.json"
            project = json.loads(project_path.read_text(encoding="utf-8"))
            project["operations"][0]["audit_policy"] = ".bima/other.json"
            project_path.write_text(json.dumps(project), encoding="utf-8")
            self.commit(subject, "switch audit policy path")
            run = self.run_launcher(
                infra, subject, evidence,
                self.environment(
                    revision, BIMA_EVENT_NAME="pull_request", BIMA_BASE_SHA=base))
            self.assertEqual(run.returncode, 3, run.stderr)
            decision = self.load_evidence(evidence)
            self.assertEqual(decision["reason_code"], "AUDIT_POLICY_PATH_CHANGED")
            self.assertFalse(decision["verifier_launched"])

    def test_pull_request_requires_a_known_base_commit(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra, subject, revision, evidence = self.fixture(temporary)
            run = self.run_launcher(
                infra, subject, evidence,
                self.environment(
                    revision, BIMA_EVENT_NAME="pull_request", BIMA_BASE_SHA="f" * 40))
            self.assertEqual(run.returncode, 3, run.stderr)
            decision = self.load_evidence(evidence)
            self.assertEqual(decision["reason_code"], "PR_BASE_UNKNOWN")
            self.assertFalse(decision["verifier_launched"])

    def test_push_uses_the_checked_out_audit_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra, subject, revision, evidence = self.fixture(temporary)
            base = self.git(subject, "rev-parse", "HEAD")
            policy_path = subject / ".bima/audit.json"
            policy = json.loads(policy_path.read_bytes())
            policy["max_file_bytes"] = 1
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            head_policy = policy_path.read_bytes()
            self.commit(subject, "weaken audit policy on push")
            run = self.run_launcher(
                infra, subject, evidence,
                self.environment(
                    revision, BIMA_EVENT_NAME="push", BIMA_BASE_SHA=base))
            self.assertEqual(run.returncode, 1, run.stderr)
            result = json.loads(
                (subject / ".artifacts/policy-gate/audit/result.json")
                .read_text(encoding="utf-8"))
            self.assertEqual(
                result["policy_sha256"], hashlib.sha256(head_policy).hexdigest())

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
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn(
            "BIMA_BASE_SHA: ${{ github.event.pull_request.base.sha }}", workflow)
        self.assertNotIn("base-sha:", workflow)

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


    def run_check(self, infra):
        return subprocess.run(
            [sys.executable, "-I", str(infra / LAUNCHER_RELATIVE),
             "--check", "--infra-root", str(infra)],
            capture_output=True, text=True, timeout=60,
        )

    def fresh_infra(self, temporary):
        infra = Path(temporary) / "infra"
        self.copy_checkout(infra)
        return infra

    def test_check_passes_for_committed_bundles(self):
        with tempfile.TemporaryDirectory() as temporary:
            run = self.run_check(self.fresh_infra(temporary))
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout.strip(), "trust-bundles: pass; bundles=1")

    def test_check_rejects_tampered_policy_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra = self.fresh_infra(temporary)
            policy_path = infra / "policies/repository-audit/dev-infra.v1.json"
            policy_path.write_bytes(policy_path.read_bytes() + b"\n")
            run = self.run_check(infra)
            self.assertEqual(run.returncode, 2, run.stdout)
            self.assertIn("TRUSTED_POLICY_HASH_MISMATCH", run.stderr)

    def test_check_rejects_missing_trusted_workflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra = self.fresh_infra(temporary)
            (infra / ".github/workflows/trusted-repository-audit.yml").unlink()
            run = self.run_check(infra)
            self.assertEqual(run.returncode, 2, run.stdout)
            self.assertIn("trusted workflow", run.stderr)

    def test_check_rejects_unknown_bundle_operation(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra = self.fresh_infra(temporary)
            bundle_path = infra / "policies/trust-bundles" / f"{BUNDLE_ID}.json"
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            bundle["operation_id"] = "unknown-operation"
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            run = self.run_check(infra)
            self.assertEqual(run.returncode, 2, run.stdout)
            self.assertIn("POLICY_OPERATION_MISSING", run.stderr)

    def test_check_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            infra = self.fresh_infra(temporary)
            bundle_path = infra / "policies/trust-bundles" / f"{BUNDLE_ID}.json"
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            bundle["policy_path"] = "../outside.json"
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            run = self.run_check(infra)
            self.assertEqual(run.returncode, 2, run.stdout)
            self.assertIn("INVALID_TRUST_PATH", run.stderr)


if __name__ == "__main__":
    unittest.main()
