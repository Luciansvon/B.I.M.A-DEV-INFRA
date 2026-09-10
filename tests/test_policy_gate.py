import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "automation" / "policy_gate.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "policy-gate"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("policy_gate", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class PolicyGateTests(unittest.TestCase):
    def setUp(self):
        self.project = {
            "schema": "bima-project.v1",
            "project_id": "example",
            "repository": "owner/example",
            "operations": [{
                "id": "repository-audit",
                "command_ref": "repository-audit.v1",
                "required": True,
                "timeout_seconds": 120,
                "output_root": ".artifacts/gate",
                "audit_policy": ".bima/audit.json",
            }],
        }
        self.policy = {
            "schema": "bima-policy.v1",
            "policy_id": "local-verify",
            "revision": "policy-1",
            "projects": [{"project_id": "example", "repository": "owner/example"}],
            "operations": [{
                "id": "repository-audit",
                "command_ref": "repository-audit.v1",
                "max_timeout_seconds": 120,
                "output_roots": [".artifacts/gate"],
                "network_destinations": [],
                "credential_names": [],
                "max_attempts": 1,
            }],
            "budget": {"max_calls": 1, "max_runtime_seconds": 120},
        }
        self.request = {
            "schema": "bima-operation-request.v1",
            "request_id": "request-1",
            "project_id": "example",
            "subject_revision": "a" * 40,
            "operation_id": "repository-audit",
            "command_ref": "repository-audit.v1",
            "output_root": ".artifacts/gate",
            "timeout_seconds": 120,
            "network_destinations": [],
            "credential_names": [],
            "attempt": 1,
            "idempotency_key": "example-audit-1",
        }
        self.policy_raw = gate.canonical_bytes(self.policy)
        self.policy_hash = hashlib.sha256(self.policy_raw).hexdigest()

    def decide(self, **replacements):
        values = {
            "project": self.project,
            "policy": self.policy,
            "request": self.request,
            "expected_policy_sha256": self.policy_hash,
            "actor": "trusted-test-runner",
            "issued_at": "2026-09-10T02:00:00Z",
            "expires_at": "2026-09-10T02:05:00Z",
            "policy_raw": self.policy_raw,
        }
        values.update(replacements)
        return gate.evaluate(**values)

    def test_matching_bounded_request_is_allowed(self):
        decision = self.decide()
        self.assertEqual(decision["decision"], "ALLOW")
        self.assertEqual(decision["reason_code"], "MATCHED_REPOSITORY_AUDIT_RULE")
        self.assertEqual(decision["request_digest"], gate.digest(self.request))
        self.assertEqual(decision["policy"]["sha256"], self.policy_hash)
        self.assertEqual(decision["approval_ref"], None)

    def test_contracts_reject_unknown_fields_and_types(self):
        cases = []
        project = copy.deepcopy(self.project)
        project["extra"] = True
        cases.append((gate.validate_project, project))
        policy = copy.deepcopy(self.policy)
        policy["budget"]["max_calls"] = True
        cases.append((gate.validate_policy, policy))
        request = copy.deepcopy(self.request)
        request["timeout_seconds"] = "120"
        cases.append((gate.validate_request, request))
        decision = self.decide()
        decision["extra"] = True
        cases.append((gate.validate_decision, decision))
        for validator, value in cases:
            with self.subTest(validator=validator.__name__):
                with self.assertRaises(gate.ContractError):
                    validator(value)

    def test_policy_hash_mismatch_fails_closed(self):
        changed = copy.deepcopy(self.policy)
        changed["projects"].append({"project_id": "attacker", "repository": "attacker/repo"})
        raw = gate.canonical_bytes(changed)
        decision = self.decide(policy=changed, policy_raw=raw)
        self.assertEqual(decision["decision"], "DENY")
        self.assertEqual(decision["reason_code"], "UNTRUSTED_POLICY_HASH")

    def test_project_declaration_cannot_elevate_resources(self):
        request = copy.deepcopy(self.request)
        request["network_destinations"] = ["example.invalid"]
        request["credential_names"] = ["ADMIN_TOKEN"]
        decision = self.decide(request=request)
        self.assertEqual(decision["decision"], "DENY")
        self.assertEqual(decision["reason_code"], "RESOURCE_SCOPE_DENIED")

    def test_project_id_cannot_spoof_policy_repository(self):
        project = copy.deepcopy(self.project)
        project["repository"] = "attacker/repo"
        decision = self.decide(project=project)
        self.assertEqual(decision["decision"], "DENY")
        self.assertEqual(decision["reason_code"], "PROJECT_NOT_ALLOWED")

    def test_output_timeout_and_attempt_are_enforced(self):
        cases = [
            ("output_root", "outside", "OUTPUT_SCOPE_DENIED"),
            ("timeout_seconds", 121, "TIMEOUT_BUDGET_EXCEEDED"),
            ("attempt", 2, "ATTEMPT_BUDGET_EXCEEDED"),
        ]
        for field, value, reason in cases:
            with self.subTest(field=field):
                request = copy.deepcopy(self.request)
                request[field] = value
                decision = self.decide(request=request)
                self.assertEqual(decision["decision"], "DENY")
                self.assertEqual(decision["reason_code"], reason)

    def test_request_binding_changes_when_scope_changes(self):
        original = self.decide()
        changed = copy.deepcopy(self.request)
        changed["idempotency_key"] = "example-audit-2"
        replacement = self.decide(request=changed)
        self.assertNotEqual(original["request_digest"], replacement["request_digest"])
        self.assertNotEqual(original["decision_id"], replacement["decision_id"])

    def test_unknown_operation_is_denied(self):
        project = copy.deepcopy(self.project)
        policy = copy.deepcopy(self.policy)
        request = copy.deepcopy(self.request)
        for document in (project["operations"][0], policy["operations"][0]):
            document["id"] = "unknown"
            document["command_ref"] = "unknown.v1"
        request["operation_id"] = "unknown"
        request["command_ref"] = "unknown.v1"
        raw = gate.canonical_bytes(policy)
        decision = self.decide(project=project, policy=policy, request=request,
                               policy_raw=raw,
                               expected_policy_sha256=hashlib.sha256(raw).hexdigest())
        self.assertEqual(decision["decision"], "DENY")
        self.assertEqual(decision["reason_code"], "UNSUPPORTED_OPERATION")

    def test_strict_json_rejects_duplicates_and_nonfinite_values(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'\xff'):
            with self.subTest(raw=raw):
                with self.assertRaises(gate.ContractError):
                    gate.strict_json(raw)

    def test_checked_in_positive_and_negative_fixtures(self):
        project, _ = gate.load_document(FIXTURES / "project.json")
        policy, policy_raw = gate.load_document(FIXTURES / "policy.json")
        policy_hash = hashlib.sha256(policy_raw).hexdigest()
        allow, _ = gate.load_document(FIXTURES / "request-allow.json")
        deny, _ = gate.load_document(FIXTURES / "request-deny-network.json")
        common = (project, policy, policy_hash, "trusted-test-runner",
                  "2026-09-10T02:00:00Z", "2026-09-10T02:05:00Z")
        self.assertEqual(gate.evaluate(common[0], common[1], allow, *common[2:], policy_raw)["decision"], "ALLOW")
        rejected = gate.evaluate(common[0], common[1], deny, *common[2:], policy_raw)
        self.assertEqual(rejected["decision"], "DENY")
        self.assertEqual(rejected["reason_code"], "RESOURCE_SCOPE_DENIED")

    def test_isolated_cli_loads_sibling_adapter_and_preserves_deny_exit(self):
        policy_hash = hashlib.sha256((FIXTURES / "policy.json").read_bytes()).hexdigest()
        run = subprocess.run([
            sys.executable, "-I", str(SCRIPT),
            "--root", str(SCRIPT.parents[1]),
            "--project", str(FIXTURES / "project.json"),
            "--trusted-policy", str(FIXTURES / "policy.json"),
            "--request", str(FIXTURES / "request-deny-network.json"),
            "--expected-policy-sha256", policy_hash,
            "--actor", "trusted-test-runner",
            "--issued-at", "2026-09-10T00:00:00Z",
            "--expires-at", "2026-09-10T23:59:59Z",
        ], capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 3, run.stderr)
        self.assertIn("DENY; reason=RESOURCE_SCOPE_DENIED", run.stdout)

    def test_executor_writes_decision_and_runs_existing_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "subject"
            root.mkdir()
            self.git(root, "init", "-q")
            self.put(root, ".gitignore", ".artifacts/\n")
            self.put(root, "README.md", "# Example\n")
            self.put(root, "AGENTS.md", "# Instructions\n")
            self.put(root, ".bima/audit.json", json.dumps({
                "schema_version": 1,
                "required_files": ["README.md", "AGENTS.md"],
                "max_file_bytes": 1048576,
            }) + "\n")
            self.git(root, "add", ".")
            self.git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                     "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
            self.request["subject_revision"] = self.git(root, "rev-parse", "HEAD")
            issued_at, expires_at = self.execution_window()
            decision, result = gate.execute_repository_audit(
                root, self.project, self.policy, self.request, self.policy_hash,
                "trusted-test-runner", issued_at, expires_at,
                self.policy_raw)
            self.assertEqual(decision["decision"], "ALLOW")
            self.assertEqual(result["status"], "pass")
            output = root / ".artifacts/gate"
            self.assertTrue((output / "decision.json").is_file())
            self.assertTrue((output / "audit/result.json").is_file())
            written = json.loads((output / "decision.json").read_text(encoding="utf-8"))
            self.assertEqual(written["request_digest"], gate.digest(self.request))

    def test_executor_denies_wrong_or_dirty_subject(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "subject"
            root.mkdir()
            self.git(root, "init", "-q")
            self.put(root, ".gitignore", ".artifacts/\n")
            self.put(root, "README.md", "# Example\n")
            self.put(root, "AGENTS.md", "# Instructions\n")
            self.put(root, ".bima/audit.json", json.dumps({
                "schema_version": 1,
                "required_files": ["README.md", "AGENTS.md"],
                "max_file_bytes": 1048576,
            }))
            self.git(root, "add", ".")
            self.git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                     "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
            self.request["subject_revision"] = "b" * 40
            issued_at, expires_at = self.execution_window()
            decision, result = gate.execute_repository_audit(
                root, self.project, self.policy, self.request, self.policy_hash,
                "trusted-test-runner", issued_at, expires_at,
                self.policy_raw)
            self.assertEqual(decision["reason_code"], "SUBJECT_REVISION_MISMATCH")
            self.assertIsNone(result)

            self.request["subject_revision"] = self.git(root, "rev-parse", "HEAD")
            self.put(root, "README.md", "dirty\n")
            decision, result = gate.execute_repository_audit(
                root, self.project, self.policy, self.request, self.policy_hash,
                "trusted-test-runner", issued_at, expires_at,
                self.policy_raw)
            self.assertEqual(decision["reason_code"], "DIRTY_SUBJECT")
            self.assertIsNone(result)

    def test_executor_denies_inactive_decision_window(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "subject"
            root.mkdir()
            self.git(root, "init", "-q")
            self.put(root, ".gitignore", ".artifacts/\n")
            self.put(root, "README.md", "# Example\n")
            self.put(root, "AGENTS.md", "# Instructions\n")
            self.put(root, ".bima/audit.json", json.dumps({
                "schema_version": 1,
                "required_files": ["README.md", "AGENTS.md"],
                "max_file_bytes": 1048576,
            }))
            self.git(root, "add", ".")
            self.git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                     "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
            self.request["subject_revision"] = self.git(root, "rev-parse", "HEAD")
            decision, result = gate.execute_repository_audit(
                root, self.project, self.policy, self.request, self.policy_hash,
                "trusted-test-runner", "2020-01-01T00:00:00Z", "2020-01-01T00:05:00Z",
                self.policy_raw)
            self.assertEqual(decision["decision"], "DENY")
            self.assertEqual(decision["reason_code"], "DECISION_WINDOW_INACTIVE")
            self.assertIsNone(result)

    @staticmethod
    def put(root, name, content):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def git(root, *args):
        return subprocess.run(["git", "-C", str(root), *args], check=True,
                              capture_output=True, text=True, timeout=30).stdout.strip()

    @staticmethod
    def execution_window():
        now = datetime.now(timezone.utc).replace(microsecond=0)
        issued = (now - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        expires = (now + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return issued, expires


if __name__ == "__main__":
    unittest.main()
