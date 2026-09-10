import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "known_failure_registry.py"
NORMALIZER_SCRIPT = ROOT / "automation" / "result_normalizer.py"
RESULT_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "result-normalizer"
REGISTRY_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "known-failure-registry" / "registry.json"
)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


registry_module = load_module("known_failure_registry", SCRIPT)
normalizer = load_module("known_failure_normalizer_fixture", NORMALIZER_SCRIPT)


class KnownFailureRegistryTests(unittest.TestCase):
    def setUp(self):
        request = json.loads(
            (RESULT_FIXTURES / "request-pass.json").read_text(encoding="utf-8")
        )
        native = (
            b"test result: FAILED. 28 passed; 1 failed; 0 ignored; "
            b"0 measured; 0 filtered out;\n"
        )
        failure = (
            Path(__file__).resolve().parent
            / "fixtures" / "known-failure-registry" / "same-attempt-diagnostic.log"
        ).read_bytes()
        request["project"] = {
            "id": "dev-infra-fixture",
            "repository": "Luciansvon/B.I.M.A-DEV-INFRA",
        }
        request["check"]["id"] = "fixture-rust-tests"
        request["environment"]["toolchain"] = "rust-fixture-v1"
        pass_native = (RESULT_FIXTURES / "rust-pass.log").read_bytes()
        pass_request = copy.deepcopy(request)
        pass_request["sources"] = {
            "native_output_sha256": hashlib.sha256(pass_native).hexdigest(),
            "failure_log_sha256": None,
        }
        self.pass_result = normalizer.normalize(pass_request, pass_native)
        request["exit_code"] = 1
        request["sources"] = {
            "native_output_sha256": hashlib.sha256(native).hexdigest(),
            "failure_log_sha256": hashlib.sha256(failure).hexdigest(),
        }
        self.result = normalizer.normalize(request, native, failure)
        self.registry = json.loads(REGISTRY_FIXTURE.read_text(encoding="utf-8"))

    def test_active_exact_match_routes_to_machine_without_retry(self):
        output = registry_module.classify(
            self.result, self.registry, "2026-09-15T00:00:00Z"
        )
        self.assertEqual(output["classification"], "known_failure")
        self.assertEqual(output["route"], "machine")
        self.assertFalse(output["automatic_retry_allowed"])
        self.assertEqual(
            output["match"]["entry_id"], "dev-infra-synthetic-known-failure-2026-09"
        )

    def test_expired_exact_match_routes_to_agent(self):
        output = registry_module.classify(
            self.result, self.registry, "2026-10-10T00:00:00Z"
        )
        self.assertEqual(output["classification"], "expired_match")
        self.assertEqual(output["route"], "agent")
        self.assertFalse(output["automatic_retry_allowed"])

    def test_not_yet_created_match_routes_to_agent(self):
        output = registry_module.classify(
            self.result, self.registry, "2026-09-09T23:59:59Z"
        )
        self.assertEqual(output["classification"], "inactive_match")
        self.assertEqual(output["route"], "agent")

    def test_changed_message_scope_or_missing_diagnostic_does_not_match(self):
        variants = []
        changed_message = copy.deepcopy(self.result)
        changed_message["diagnostics"][0]["message"] += " changed"
        variants.append(changed_message)
        changed_scope = copy.deepcopy(self.result)
        changed_scope["environment"]["toolchain"] = "rust-stable-next"
        variants.append(changed_scope)
        missing_diagnostic = copy.deepcopy(self.result)
        missing_diagnostic["diagnostics"].pop()
        variants.append(missing_diagnostic)
        dirty_subject = copy.deepcopy(self.result)
        dirty_subject["identity"]["subject_dirty"] = True
        variants.append(dirty_subject)
        changed_equivalence = copy.deepcopy(self.result)
        changed_equivalence["attempt"]["equivalence_key"] = "different-reset-state"
        changed_equivalence["stability"]["equivalence_key"] = "different-reset-state"
        variants.append(changed_equivalence)
        changed_expectation = copy.deepcopy(self.result)
        changed_expectation["outcome"]["expected_tests"] = 30
        variants.append(changed_expectation)
        for variant in variants:
            with self.subTest(variant=variant):
                output = registry_module.classify(
                    variant, self.registry, "2026-09-15T00:00:00Z"
                )
                self.assertEqual(output["classification"], "unmatched")
                self.assertEqual(output["route"], "agent")

    def test_pass_is_not_applicable_even_if_registry_matches_scope(self):
        output = registry_module.classify(
            self.pass_result, self.registry, "2026-09-15T00:00:00Z"
        )
        self.assertEqual(output["classification"], "not_applicable")
        self.assertEqual(output["route"], "none")
        self.assertIsNone(output["match"])

    def test_owner_review_expiry_and_validity_cap_are_enforced(self):
        for field in ("owner", "reviewed_by", "expires_at"):
            registry = copy.deepcopy(self.registry)
            registry["entries"][0][field] = ""
            with self.subTest(field=field), self.assertRaises(registry_module.RegistryError):
                registry_module.validate_registry(registry)
        registry = copy.deepcopy(self.registry)
        registry["entries"][0]["expires_at"] = "2027-01-01T00:00:00Z"
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_registry(registry)

    def test_duplicate_match_and_unsorted_signatures_are_rejected(self):
        registry = copy.deepcopy(self.registry)
        duplicate = copy.deepcopy(registry["entries"][0])
        duplicate["id"] = "second-entry"
        registry["entries"].append(duplicate)
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_registry(registry)
        registry = copy.deepcopy(self.registry)
        registry["entries"][0]["diagnostic_signatures"].append({
            "tool": "typescript",
            "code": "TS0000",
            "path": "tests/known_failure.ts",
            "message_sha256": "0" * 64,
        })
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_registry(registry)

    def test_duplicate_nonfinite_and_unknown_fields_fail_closed(self):
        with self.assertRaises(registry_module.RegistryError):
            registry_module.strict_json(b'{"schema":"x","schema":"y"}')
        with self.assertRaises(registry_module.RegistryError):
            registry_module.strict_json(b'{"number":NaN}')
        registry = copy.deepcopy(self.registry)
        registry["entries"][0]["automatic_retry"] = True
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_registry(registry)

    def test_malformed_result_counts_and_verdict_fail_closed(self):
        result = copy.deepcopy(self.result)
        result["outcome"]["counts"]["failed"] = 0
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_result(result)
        result = copy.deepcopy(self.result)
        result["execution"]["exit_code"] = 0
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_result(result)

    def test_canonical_classification_is_deterministic(self):
        first = registry_module.classify(
            self.result, self.registry, "2026-09-15T00:00:00Z"
        )
        second = registry_module.classify(
            self.result, self.registry, "2026-09-15T00:00:00Z"
        )
        self.assertEqual(
            registry_module.canonical_bytes(first), registry_module.canonical_bytes(second)
        )

    def test_cli_writes_bounded_classification(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            result_path = temporary_path / "result.json"
            result_path.write_bytes(registry_module.canonical_bytes(self.result))
            output_path = temporary_path / "output"
            run = subprocess.run(
                [
                    sys.executable, "-I", str(SCRIPT),
                    "--result", str(result_path),
                    "--registry", str(REGISTRY_FIXTURE),
                    "--as-of", "2026-09-15T00:00:00Z",
                    "--output", str(output_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            output = json.loads(
                (output_path / "classification.json").read_text(encoding="utf-8")
            )
            self.assertEqual(output["classification"], "known_failure")
            self.assertIn("automatic_retry_allowed=false", run.stdout)


if __name__ == "__main__":
    unittest.main()
