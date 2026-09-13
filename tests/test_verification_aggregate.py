import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "verification_aggregate.py"
NORMALIZER_SCRIPT = ROOT / "automation" / "result_normalizer.py"
FIXTURES = ROOT / "tests" / "fixtures" / "result-normalizer"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


aggregate_module = load_module("verification_aggregate", SCRIPT)
normalizer = load_module("verification_aggregate_normalizer", NORMALIZER_SCRIPT)


class VerificationAggregateTests(unittest.TestCase):
    def setUp(self):
        request = json.loads(
            (FIXTURES / "request-pass.json").read_text(encoding="utf-8")
        )
        native = (FIXTURES / "rust-pass.log").read_bytes()
        self.result = normalizer.normalize(request, native)
        self.plan = {
            "schema": "bima-verification-plan.v1",
            "aggregate_id": "release-required-checks",
            "project": {
                "id": self.result["identity"]["project_id"],
                "repository": self.result["identity"]["repository"],
            },
            "subject": {
                "revision": self.result["identity"]["subject_revision"],
                "dirty": self.result["identity"]["subject_dirty"],
            },
            "policy": copy.deepcopy(self.result["policy"]),
            "required_checks": [self.result["identity"]["check_id"]],
            "optional_checks": [],
        }

    def variant(self, check_id, verdict, applicability="required", stability="unassessed"):
        result = copy.deepcopy(self.result)
        result["identity"]["check_id"] = check_id
        result["applicability"] = applicability
        result["verdict"] = verdict
        result["outcome"]["value"] = {
            "PASS": "pass",
            "FAIL": "fail",
            "UNKNOWN": "unknown",
            "BLOCKED": "not_run",
        }[verdict]
        result["outcome"]["reason_code"] = f"FIXTURE_{verdict}"
        result["stability"]["value"] = stability
        if verdict == "FAIL":
            result["execution"]["exit_code"] = 1
            result["outcome"]["counts"]["passed"] = 28
            result["outcome"]["counts"]["failed"] = 1
            result["outcome"]["observed_tests"] = 29
            result["outcome"]["suites"] = [{
                "status": "failed", "passed": 28, "failed": 1,
                "ignored": 0, "measured": 0, "filtered_out": 0,
            }]
        elif verdict == "BLOCKED":
            result["execution"]["exit_code"] = 1
            result["outcome"]["observed_tests"] = 0
            result["outcome"]["counts"] = {
                "passed": 0, "failed": 0, "ignored": 0,
                "measured": 0, "filtered_out": 0,
            }
            result["outcome"]["suites"] = []
        return result

    def test_all_required_pass(self):
        report = aggregate_module.aggregate(self.plan, [self.result])
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["reason_code"], "ALL_REQUIRED_CHECKS_PASSED")
        self.assertEqual(report["counts"]["required"]["pass"], 1)
        self.assertEqual(report["unresolved_required"], [])

    def test_required_fail_wins_over_blocked_and_unknown(self):
        plan = copy.deepcopy(self.plan)
        plan["required_checks"] = ["build", "lint", "rust-core-tests"]
        results = [
            self.variant("build", "BLOCKED"),
            self.variant("lint", "UNKNOWN"),
            self.variant("rust-core-tests", "FAIL"),
        ]
        report = aggregate_module.aggregate(plan, results)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["reason_code"], "REQUIRED_CHECK_FAILED")
        self.assertEqual(report["unresolved_required"], ["build", "lint", "rust-core-tests"])

    def test_required_blocked_wins_over_missing_or_unknown(self):
        plan = copy.deepcopy(self.plan)
        plan["required_checks"] = ["build", "lint", "rust-core-tests"]
        results = [
            self.variant("build", "BLOCKED"),
            self.variant("lint", "UNKNOWN"),
        ]
        report = aggregate_module.aggregate(plan, results)
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertEqual(report["reason_code"], "REQUIRED_CHECK_BLOCKED")
        self.assertEqual(report["counts"]["required"]["missing"], 1)

    def test_missing_required_evidence_is_unknown(self):
        plan = copy.deepcopy(self.plan)
        plan["required_checks"] = ["build", "rust-core-tests"]
        report = aggregate_module.aggregate(plan, [self.result])
        self.assertEqual(report["verdict"], "UNKNOWN")
        self.assertEqual(report["reason_code"], "REQUIRED_EVIDENCE_MISSING")
        self.assertEqual(report["unresolved_required"], ["build"])

    def test_no_results_marks_every_required_check_missing(self):
        report = aggregate_module.aggregate(self.plan, [])
        self.assertEqual(report["verdict"], "UNKNOWN")
        self.assertEqual(report["reason_code"], "REQUIRED_EVIDENCE_MISSING")
        self.assertEqual(report["counts"]["required"]["reported"], 0)
        self.assertEqual(report["counts"]["required"]["missing"], 1)

    def test_required_unknown_and_flaky_are_unknown(self):
        unknown = aggregate_module.aggregate(
            self.plan, [self.variant("rust-core-tests", "UNKNOWN")]
        )
        self.assertEqual(unknown["reason_code"], "REQUIRED_CHECK_UNKNOWN")
        flaky = aggregate_module.aggregate(
            self.plan,
            [self.variant("rust-core-tests", "PASS", stability="flaky")],
        )
        self.assertEqual(flaky["verdict"], "UNKNOWN")
        self.assertEqual(flaky["reason_code"], "REQUIRED_CHECK_FLAKY")

    def test_optional_non_pass_stays_visible_without_blocking_pass(self):
        plan = copy.deepcopy(self.plan)
        plan["optional_checks"] = ["typescript"]
        optional = self.variant("typescript", "FAIL", applicability="optional")
        report = aggregate_module.aggregate(plan, [self.result, optional])
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["optional_non_pass"], ["typescript"])
        self.assertEqual(report["counts"]["optional"]["fail"], 1)

    def test_missing_optional_result_stays_visible_without_blocking_pass(self):
        plan = copy.deepcopy(self.plan)
        plan["optional_checks"] = ["typescript"]
        report = aggregate_module.aggregate(plan, [self.result])
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["optional_non_pass"], ["typescript"])
        self.assertEqual(report["counts"]["optional"]["missing"], 1)

    def test_wrong_subject_project_policy_and_applicability_fail_closed(self):
        variants = []
        wrong_subject = copy.deepcopy(self.result)
        wrong_subject["identity"]["subject_revision"] = "f" * 40
        variants.append((self.plan, [wrong_subject]))
        wrong_project = copy.deepcopy(self.result)
        wrong_project["identity"]["project_id"] = "wrong-project"
        variants.append((self.plan, [wrong_project]))
        wrong_policy = copy.deepcopy(self.result)
        wrong_policy["policy"]["sha256"] = "f" * 64
        variants.append((self.plan, [wrong_policy]))
        wrong_applicability = copy.deepcopy(self.result)
        wrong_applicability["applicability"] = "optional"
        variants.append((self.plan, [wrong_applicability]))
        for plan, results in variants:
            with self.subTest(result=results[-1]), self.assertRaises(aggregate_module.AggregateError):
                aggregate_module.aggregate(plan, results)

    def test_duplicate_and_undeclared_results_fail_closed(self):
        with self.assertRaises(aggregate_module.AggregateError):
            aggregate_module.aggregate(self.plan, [self.result, self.result])
        undeclared = copy.deepcopy(self.result)
        undeclared["identity"]["check_id"] = "undeclared"
        with self.assertRaises(aggregate_module.AggregateError):
            aggregate_module.aggregate(self.plan, [undeclared])

    def test_plan_requires_sorted_disjoint_nonempty_required_checks(self):
        variants = []
        unsorted = copy.deepcopy(self.plan)
        unsorted["required_checks"] = ["z-check", "a-check"]
        variants.append(unsorted)
        overlap = copy.deepcopy(self.plan)
        overlap["optional_checks"] = overlap["required_checks"][:]
        variants.append(overlap)
        empty = copy.deepcopy(self.plan)
        empty["required_checks"] = []
        variants.append(empty)
        for plan in variants:
            with self.subTest(plan=plan), self.assertRaises(aggregate_module.AggregateError):
                aggregate_module.validate_plan(plan)

    def test_strict_json_rejects_duplicate_nonfinite_and_unknown_fields(self):
        with self.assertRaises(aggregate_module.AggregateError):
            aggregate_module.strict_json(b'{"schema":"x","schema":"y"}')
        with self.assertRaises(aggregate_module.AggregateError):
            aggregate_module.strict_json(b'{"value":NaN}')
        plan = copy.deepcopy(self.plan)
        plan["unknown"] = True
        with self.assertRaises(aggregate_module.AggregateError):
            aggregate_module.validate_plan(plan)

    def test_malformed_result_content_fails_closed(self):
        variants = []
        wrong_counts = copy.deepcopy(self.result)
        wrong_counts["outcome"]["counts"]["passed"] -= 1
        variants.append(wrong_counts)
        wrong_source = copy.deepcopy(self.result)
        wrong_source["sources"][0]["role"] = "unknown"
        variants.append(wrong_source)
        wrong_outcome = copy.deepcopy(self.result)
        wrong_outcome["outcome"]["value"] = "fail"
        variants.append(wrong_outcome)
        for result in variants:
            with self.subTest(result=result), self.assertRaises(aggregate_module.AggregateError):
                aggregate_module.aggregate(self.plan, [result])

    def test_canonical_output_is_deterministic(self):
        first = aggregate_module.aggregate(self.plan, [self.result])
        second = aggregate_module.aggregate(self.plan, [self.result])
        self.assertEqual(
            aggregate_module.canonical_bytes(first),
            aggregate_module.canonical_bytes(second),
        )

    def test_cli_writes_report_and_preserves_verdict_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root / "plan.json"
            result = root / "result.json"
            output = root / "output"
            plan.write_bytes(aggregate_module.canonical_bytes(self.plan))
            result.write_bytes(aggregate_module.canonical_bytes(self.result))
            run = subprocess.run(
                [
                    sys.executable, "-I", str(SCRIPT),
                    "--plan", str(plan),
                    "--result", str(result),
                    "--output", str(output),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads(
                (output / "aggregate.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["verdict"], "PASS")
            self.assertIn("required=1/1", run.stdout)

    def test_cli_zero_results_writes_unknown_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root / "plan.json"
            output = root / "output"
            plan.write_bytes(aggregate_module.canonical_bytes(self.plan))
            run = subprocess.run(
                [
                    sys.executable, "-I", str(SCRIPT),
                    "--plan", str(plan),
                    "--output", str(output),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(run.returncode, 2, run.stderr)
            report = json.loads(
                (output / "aggregate.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["verdict"], "UNKNOWN")
            self.assertEqual(report["reason_code"], "REQUIRED_EVIDENCE_MISSING")


if __name__ == "__main__":
    unittest.main()
