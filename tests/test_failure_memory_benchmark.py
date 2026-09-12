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
SCRIPT = ROOT / "automation/failure_memory_benchmark.py"
RECORDS_SCRIPT = ROOT / "automation/failure_records.py"
FIXTURE = ROOT / "tests/fixtures/failure-records/records.json"
PRODUCTION_RECORDS = ROOT / "failure-records/records.json"
PRODUCTION_QUERIES = ROOT / "benchmarks/failure-memory/held-out.json"

BENCHMARK_SPEC = importlib.util.spec_from_file_location("failure_memory_benchmark", SCRIPT)
benchmark_module = importlib.util.module_from_spec(BENCHMARK_SPEC)
BENCHMARK_SPEC.loader.exec_module(benchmark_module)
RECORDS_SPEC = importlib.util.spec_from_file_location("benchmark_failure_records", RECORDS_SCRIPT)
records_module = importlib.util.module_from_spec(RECORDS_SPEC)
RECORDS_SPEC.loader.exec_module(records_module)


class FailureMemoryBenchmarkTests(unittest.TestCase):
    def setUp(self):
        fixture = records_module.load_document(FIXTURE)
        template = fixture["records"][0]
        records = []
        for index in range(101):
            record = copy.deepcopy(template)
            record["id"] = f"case-{index:03d}"
            record["case_kind"] = "real"
            record["failure"]["signature_sha256"] = f"{index + 1:064x}"
            record["cause"]["summary"] = f"Unique retrieval token needle{index:03d}."
            records.append(record)
        records[99]["access"] = {
            "classification": "restricted",
            "allowed_projects": ["other-project"],
        }
        records[100]["status"] = "INVALIDATED"
        records[100]["invalidation_reason"] = "Synthetic stale benchmark case."
        self.corpus = {
            "schema": "bima-failure-record-set.v1",
            "dataset_id": "benchmark-test-corpus",
            "records": records,
        }
        digest = hashlib.sha256(records_module.canonical_bytes(self.corpus)).hexdigest()
        self.request = {
            "schema": "bima-failure-memory-benchmark-request.v1",
            "benchmark_id": "benchmark-test",
            "dataset_id": "benchmark-test-corpus",
            "record_set_sha256": digest,
            "held_out": True,
            "acceptance": {
                "k": 5,
                "minimum_recall_ppm": 1_000_000,
                "minimum_mrr_ppm": 1_000_000,
                "maximum_false_match_ppm": 0,
                "maximum_stale_hit_ppm": 0,
            },
            "queries": [
                {
                    "id": f"query-{index:03d}",
                    "text": f"needle{index:03d}",
                    "project_id": "fixture-project",
                    "relevant_record_ids": [f"case-{index:03d}"],
                    "forbidden_record_ids": ["case-099", "case-100"],
                }
                for index in range(10)
            ],
        }

    def test_production_benchmark_is_blocked_without_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            database = temporary / "benchmark.sqlite3"
            report = temporary / "report.json"
            run = subprocess.run(
                [
                    sys.executable, "-I", str(SCRIPT),
                    "--records", str(PRODUCTION_RECORDS),
                    "--queries", str(PRODUCTION_QUERIES),
                    "--database", str(database),
                    "--repository-root", str(ROOT),
                    "--report", str(report),
                ],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(run.returncode, 3, run.stderr)
            result = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(result["reason_code"], "INSUFFICIENT_REAL_CASES")
            self.assertIsNone(result["metrics"])
            self.assertFalse(database.exists())

    def test_exact_held_out_queries_pass_all_metrics(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "benchmark.sqlite3"
            report = benchmark_module.benchmark(self.corpus, self.request, database, ROOT)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["metrics"], {
                "recall_at_k_ppm": 1_000_000,
                "mrr_ppm": 1_000_000,
                "false_match_ppm": 0,
                "stale_hit_ppm": 0,
            })
            self.assertTrue(report["database_created"])

    def test_acceptance_failure_is_not_converted_to_pass(self):
        request = copy.deepcopy(self.request)
        for query in request["queries"]:
            query["text"] = "retrieval"
        with tempfile.TemporaryDirectory() as temporary:
            report = benchmark_module.benchmark(
                self.corpus, request, Path(temporary) / "benchmark.sqlite3", ROOT)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["reason_code"], "ACCEPTANCE_NOT_SATISFIED")
            self.assertGreater(report["metrics"]["false_match_ppm"], 0)

    def test_held_out_and_query_count_gates_block_before_build(self):
        cases = []
        request = copy.deepcopy(self.request)
        request["held_out"] = False
        cases.append((request, "HELD_OUT_QUERIES_REQUIRED"))
        request = copy.deepcopy(self.request)
        request["queries"] = request["queries"][:9]
        cases.append((request, "INSUFFICIENT_HELD_OUT_QUERIES"))
        for request, reason in cases:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as temporary:
                database = Path(temporary) / "benchmark.sqlite3"
                report = benchmark_module.benchmark(self.corpus, request, database, ROOT)
                self.assertEqual(report["status"], "BLOCKED")
                self.assertEqual(report["reason_code"], reason)
                self.assertFalse(database.exists())

    def test_dataset_binding_and_record_references_fail_closed(self):
        request = copy.deepcopy(self.request)
        request["record_set_sha256"] = "0" * 64
        with self.assertRaises(benchmark_module.BenchmarkError):
            benchmark_module.benchmark(self.corpus, request, Path("unused"), ROOT)
        request = copy.deepcopy(self.request)
        request["queries"][0]["relevant_record_ids"] = ["missing-record"]
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(
                benchmark_module.BenchmarkError):
            benchmark_module.benchmark(
                self.corpus, request, Path(temporary) / "benchmark.sqlite3", ROOT)

    def test_strict_contract_rejects_duplicates_nonfinite_and_overlap(self):
        with self.assertRaises(benchmark_module.BenchmarkError):
            benchmark_module.strict_json(b'{"schema":"x","schema":"y"}')
        with self.assertRaises(benchmark_module.BenchmarkError):
            benchmark_module.strict_json(b'{"value":NaN}')
        request = copy.deepcopy(self.request)
        request["queries"][0]["forbidden_record_ids"].append("case-000")
        request["queries"][0]["forbidden_record_ids"].sort()
        with self.assertRaises(benchmark_module.BenchmarkError):
            benchmark_module.validate_request(request)

    def test_report_bytes_are_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            report_a = benchmark_module.benchmark(
                self.corpus, self.request, Path(first) / "benchmark.sqlite3", ROOT)
            report_b = benchmark_module.benchmark(
                self.corpus, self.request, Path(second) / "benchmark.sqlite3", ROOT)
            self.assertEqual(
                benchmark_module.canonical_bytes(report_a),
                benchmark_module.canonical_bytes(report_b),
            )


if __name__ == "__main__":
    unittest.main()
