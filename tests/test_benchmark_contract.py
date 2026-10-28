import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "automation" / "benchmark_contract.py"
SPEC = importlib.util.spec_from_file_location("benchmark_contract", SCRIPT)
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


class BenchmarkContractTests(unittest.TestCase):
    def test_strict_json_rejects_duplicates_and_non_finite(self):
        with self.assertRaises(contract.BenchmarkError):
            contract.strict_json(b'{"schema":"x","schema":"y"}')
        with self.assertRaises(contract.BenchmarkError):
            contract.strict_json(b'{"value":NaN}')
        self.assertEqual(
            contract.strict_json(b'{"b":1,"a":2}'), {"b": 1, "a": 2})

    def test_canonical_bytes_and_digest_are_deterministic(self):
        left = contract.canonical_bytes({"b": 1, "a": [2, 3]})
        right = contract.canonical_bytes({"a": [2, 3], "b": 1})
        self.assertEqual(left, right)
        self.assertTrue(left.endswith(b"\n"))
        self.assertEqual(len(contract.digest({"a": 1})), 64)
        self.assertNotEqual(
            contract.digest({"a": 1}), contract.digest({"a": 2}))

    def test_identifier_sha_ppm_and_sorted_id_bounds(self):
        contract.validate_identifier("case-1", "id")
        contract.validate_sha256("0" * 64, "sha")
        contract.validate_ppm(0, "score")
        contract.validate_ppm(1_000_000, "score")
        contract.validate_sorted_ids(["a", "b"], "ids")
        contract.validate_sorted_ids(["a", "b"], "ids", minimum=2)
        for value in ("Upper", "", "-lead", "a" * 65):
            with self.subTest(kind="identifier", value=value):
                with self.assertRaises(contract.BenchmarkError):
                    contract.validate_identifier(value, "id")
        for value in (-1, 1_000_001, True, 1.5):
            with self.subTest(kind="ppm", value=value):
                with self.assertRaises(contract.BenchmarkError):
                    contract.validate_ppm(value, "score")
        for value in (["b", "a"], ["a", "a"], [], ["a"] * 101):
            with self.subTest(kind="sorted", value=value):
                with self.assertRaises(contract.BenchmarkError):
                    contract.validate_sorted_ids(value, "ids", minimum=1)
        with self.assertRaises(contract.BenchmarkError):
            contract.validate_sha256("A" * 64, "sha")

    def test_exact_fields_and_strings_fail_closed(self):
        contract.validate_exact_fields({"a": 1}, {"a"}, "document")
        contract.validate_string("value", "label")
        for value in ({"a": 1, "b": 2}, {}, []):
            with self.subTest(value=value):
                with self.assertRaises(contract.BenchmarkError):
                    contract.validate_exact_fields(value, {"a"}, "document")
        for value in ("", 1, "x" * 513):
            with self.subTest(value=value):
                with self.assertRaises(contract.BenchmarkError):
                    contract.validate_string(value, "label")

    def test_load_document_requires_a_regular_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "request.json"
            path.write_bytes(b'{"a":1}')
            self.assertEqual(contract.load_document(path), {"a": 1})
            with self.assertRaises(contract.BenchmarkError):
                contract.load_document(root / "missing.json")
            with self.assertRaises(contract.BenchmarkError):
                contract.load_document(root)


if __name__ == "__main__":
    unittest.main()
