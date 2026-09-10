import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "automation" / "result_normalizer.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "result-normalizer"
SPEC = importlib.util.spec_from_file_location("result_normalizer", SCRIPT)
normalizer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(normalizer)


class ResultNormalizerTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((FIXTURES / "request-pass.json").read_text(encoding="utf-8"))
        self.native = (FIXTURES / "rust-pass.log").read_bytes()
        self.failure = (FIXTURES / "typescript-fail.log").read_bytes()

    def test_real_consumer_fixture_passes_with_all_suites_preserved(self):
        result = normalizer.normalize(self.request, self.native)
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["outcome"]["observed_tests"], 29)
        self.assertEqual(result["outcome"]["counts"]["passed"], 29)
        self.assertEqual(len(result["outcome"]["suites"]), 3)
        self.assertEqual(len(result["diagnostics"]), 0)
        self.assertEqual(result["identity"]["subject_revision"], self.request["subject"]["revision"])
        self.assertEqual(result["attempt"], self.request["attempt"])

    def test_expected_count_mismatch_is_unknown(self):
        request = copy.deepcopy(self.request)
        request["check"]["expected_tests"] = 30
        result = normalizer.normalize(request, self.native)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertEqual(result["outcome"]["reason_code"], "EXPECTED_TEST_COUNT_MISMATCH")

    def test_missing_summary_is_unknown_even_with_zero_exit(self):
        native = b"build completed\n"
        result = normalizer.normalize(self.with_sources(native), native)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertEqual(result["outcome"]["reason_code"], "MISSING_TEST_SUMMARY")

    def test_reported_test_failure_is_fail(self):
        request = copy.deepcopy(self.request)
        request["exit_code"] = 1
        raw = b"test result: FAILED. 28 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out;\n"
        request = self.with_sources(raw, request=request)
        result = normalizer.normalize(request, raw)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["outcome"]["reason_code"], "TEST_FAILURE_REPORTED")

    def test_exit_summary_disagreement_is_unknown(self):
        raw = b"test result: FAILED. 28 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out;\n"
        result = normalizer.normalize(self.with_sources(raw), raw)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertEqual(result["outcome"]["reason_code"], "EXIT_SUMMARY_DISAGREE")

    def test_nonzero_exit_without_test_failure_is_unknown(self):
        request = copy.deepcopy(self.request)
        request["exit_code"] = 1
        result = normalizer.normalize(request, self.native)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertEqual(result["outcome"]["reason_code"], "NONZERO_EXIT_WITHOUT_TEST_FAILURE")

    def test_diagnostics_are_relative_bounded_and_redacted(self):
        lines = []
        for number in range(60):
            lines.append(
                f"##[error]D:\\a\\repo\\src\\file.ts({number + 1},2): error TS2322: "
                f"token=ghp_{'A' * 30} " + "x" * 300)
        diagnostics = normalizer.parse_typescript_diagnostics("\n".join(lines))
        self.assertEqual(len(diagnostics), normalizer.MAX_DIAGNOSTICS)
        self.assertEqual(diagnostics[0]["path"], "src/file.ts")
        self.assertNotIn("ghp_", diagnostics[0]["message"])
        self.assertIn("[REDACTED]", diagnostics[0]["message"])
        self.assertLessEqual(len(diagnostics[0]["message"]), normalizer.MAX_MESSAGE_CHARS)

    def test_sources_retain_hash_and_size_not_raw_text(self):
        same_attempt_diagnostic = b"src/file.ts(1,2): error TS2322: token=secret-value\n"
        request = self.with_sources(self.native, same_attempt_diagnostic)
        result = normalizer.normalize(request, self.native, same_attempt_diagnostic)
        self.assertEqual(result["sources"][0]["sha256"], hashlib.sha256(self.native).hexdigest())
        self.assertEqual(result["sources"][1]["size_bytes"], len(same_attempt_diagnostic))
        serialized = json.dumps(result)
        self.assertNotIn("secret-value", serialized)

    def test_strict_contract_rejects_unknown_duplicate_and_oversized_input(self):
        request = copy.deepcopy(self.request)
        request["unknown"] = True
        with self.assertRaises(normalizer.NormalizationError):
            normalizer.normalize(request, self.native)
        with self.assertRaises(normalizer.NormalizationError):
            normalizer.strict_json(b'{"a":1,"a":2}')
        with self.assertRaises(normalizer.NormalizationError):
            normalizer.normalize(self.request, b"x" * (normalizer.MAX_INPUT_BYTES + 1))

    def test_canonical_bytes_are_deterministic(self):
        first = normalizer.canonical_bytes(normalizer.normalize(self.request, self.native))
        second = normalizer.canonical_bytes(normalizer.normalize(self.request, self.native))
        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n"))

    def test_isolated_cli_writes_result_and_preserves_exit_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result"
            run = subprocess.run([
                sys.executable, "-I", str(SCRIPT),
                "--request", str(FIXTURES / "request-pass.json"),
                "--native-output", str(FIXTURES / "rust-pass.log"),
                "--output", str(output),
            ], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads((output / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["verdict"], "PASS")
            self.assertIn("diagnostics=0", run.stdout)

    def test_source_substitution_is_rejected(self):
        with self.assertRaises(normalizer.NormalizationError):
            normalizer.normalize(self.request, self.native + b"changed")
        with self.assertRaises(normalizer.NormalizationError):
            normalizer.normalize(self.request, self.native, self.failure)

    def with_sources(self, native, failure=None, request=None):
        value = copy.deepcopy(request if request is not None else self.request)
        value["sources"] = {
            "native_output_sha256": hashlib.sha256(native).hexdigest(),
            "failure_log_sha256": hashlib.sha256(failure).hexdigest() if failure is not None else None,
        }
        return value


if __name__ == "__main__":
    unittest.main()
