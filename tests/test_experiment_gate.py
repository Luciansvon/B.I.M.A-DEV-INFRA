import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation/experiment_gate.py"
FIXTURE = ROOT / "tests/fixtures/experiment-gate/request-one-project.json"
SPEC = importlib.util.spec_from_file_location("experiment_gate", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class ExperimentGateTests(unittest.TestCase):
    def setUp(self):
        self.request = gate.load_document(FIXTURE)

    def add_second_project(self, request=None, capability=None):
        request = copy.deepcopy(request or self.request)
        request["demand_evidence"].append({
            "project_id": "fixture-b",
            "repository": "example/fixture-b",
            "capability": capability or request["capability"],
            "requirement_ref": "example/fixture-b#2",
            "reviewed_by": "fixture-reviewer-b",
        })
        return request

    def test_one_project_is_blocked_and_does_not_execute(self):
        decision = gate.evaluate(self.request)
        self.assertEqual(decision["status"], "BLOCKED")
        self.assertEqual(decision["reason_code"], "INSUFFICIENT_CROSS_PROJECT_DEMAND")
        self.assertFalse(decision["execution_started"])
        self.assertTrue(decision["requires_policy_authorization"])

    def test_two_projects_with_matching_capability_are_ready(self):
        request = self.add_second_project()
        request["demand_evidence"][1]["requirement_ref"] = (
            "https://github.com/example/fixture-b/issues/2")
        decision = gate.evaluate(request)
        self.assertEqual(decision["status"], "READY")
        self.assertEqual(decision["distinct_projects"], 2)
        self.assertEqual(
            {item["capability"] for item in request["demand_evidence"]},
            {request["capability"]})
        self.assertFalse(decision["execution_started"])

    def test_two_projects_with_different_capabilities_fail(self):
        with self.assertRaises(gate.ExperimentGateError):
            gate.evaluate(self.add_second_project(capability="release-proof"))

    def test_unknown_capability_fails_closed(self):
        request = copy.deepcopy(self.request)
        request["capability"] = "teleport"
        request["demand_evidence"][0]["capability"] = "teleport"
        with self.assertRaises(gate.ExperimentGateError):
            gate.validate_request(request)

    def test_duplicate_repository_and_requirement_fail(self):
        request = copy.deepcopy(self.request)
        duplicate = copy.deepcopy(request["demand_evidence"][0])
        duplicate["project_id"] = "second-project"
        request["demand_evidence"].append(duplicate)
        with self.assertRaisesRegex(gate.ExperimentGateError, "repository and requirement"):
            gate.validate_request(request)

    def test_placeholder_reviewer_and_requirement_ref_fail(self):
        for reviewer in ("", "TBD", " reviewer "):
            request = copy.deepcopy(self.request)
            request["demand_evidence"][0]["reviewed_by"] = reviewer
            with self.subTest(reviewed_by=reviewer), self.assertRaises(gate.ExperimentGateError):
                gate.validate_request(request)
        for reference in ("", "TBD", "fixture://fixture-a/requirement",
                          "https://", "example/fixture-a"):
            request = copy.deepcopy(self.request)
            request["demand_evidence"][0]["requirement_ref"] = reference
            with self.subTest(requirement_ref=reference), self.assertRaises(gate.ExperimentGateError):
                gate.validate_request(request)

    def test_duplicate_project_or_repository_cannot_inflate_demand(self):
        request = copy.deepcopy(self.request)
        second = copy.deepcopy(request["demand_evidence"][0])
        second["project_id"] = "second-project"
        second["requirement_ref"] = "example/second-project#3"
        second["reviewed_by"] = "second-reviewer"
        request["demand_evidence"].append(second)
        with self.assertRaises(gate.ExperimentGateError):
            gate.evaluate(request)

        request = copy.deepcopy(self.request)
        second = copy.deepcopy(request["demand_evidence"][0])
        second["repository"] = "example/second-project"
        second["requirement_ref"] = "example/second-project#3"
        second["reviewed_by"] = "second-reviewer"
        request["demand_evidence"].append(second)
        with self.assertRaises(gate.ExperimentGateError):
            gate.evaluate(request)

    def test_local_slm_requires_1000_verified_held_out_cases(self):
        request = copy.deepcopy(self.request)
        request["capability"] = "local-qa-slm"
        request["demand_evidence"][0]["capability"] = "local-qa-slm"
        request = self.add_second_project(request)
        request["dataset"]["verified_cases"] = 999
        decision = gate.evaluate(request)
        self.assertEqual(decision["reason_code"], "MODEL_BENCHMARK_GATE_UNMET")
        request["dataset"]["verified_cases"] = 1000
        self.assertEqual(gate.evaluate(request)["status"], "READY")
        request["dataset"]["held_out"] = False
        self.assertEqual(
            gate.evaluate(request)["reason_code"], "MODEL_BENCHMARK_GATE_UNMET")

    def test_missing_baseline_reject_rollback_and_permissions_fail_closed(self):
        cases = []
        request = copy.deepcopy(self.request)
        request["baseline"]["evidence_refs"] = []
        cases.append(request)
        request = copy.deepcopy(self.request)
        request["reject_criteria"] = []
        cases.append(request)
        request = copy.deepcopy(self.request)
        request["rollback"]["steps"] = []
        cases.append(request)
        request = copy.deepcopy(self.request)
        request["permissions"]["write_roots"] = ["../outside"]
        cases.append(request)
        for request in cases:
            with self.subTest(request=request), self.assertRaises(gate.ExperimentGateError):
                gate.validate_request(request)

    def test_duplicate_unknown_and_nonfinite_inputs_fail_closed(self):
        request = copy.deepcopy(self.request)
        request["unknown"] = True
        with self.assertRaises(gate.ExperimentGateError):
            gate.validate_request(request)
        with self.assertRaises(gate.ExperimentGateError):
            gate.strict_json(b'{"schema":"x","schema":"y"}')
        with self.assertRaises(gate.ExperimentGateError):
            gate.strict_json(b'{"number":NaN}')

    def test_decision_is_deterministic(self):
        request = self.add_second_project()
        first = gate.canonical_bytes(gate.evaluate(request))
        second = gate.canonical_bytes(gate.evaluate(request))
        self.assertEqual(first, second)

    def test_cli_writes_blocked_decision_with_exit_three(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            run = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), "--request", str(FIXTURE),
                 "--output", str(output)],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(run.returncode, 3, run.stderr)
            decision = json.loads((output / "decision.json").read_text(encoding="utf-8"))
            self.assertEqual(decision["status"], "BLOCKED")
            self.assertFalse(decision["execution_started"])


if __name__ == "__main__":
    unittest.main()
