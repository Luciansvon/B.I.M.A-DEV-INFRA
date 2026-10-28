"""Benchmark gated SQLite/FTS5 failure retrieval against held-out queries."""

import argparse
from fractions import Fraction
import importlib.util
from pathlib import Path
import sqlite3
import sys


MEMORY_SCRIPT = Path(__file__).resolve().with_name("failure_memory.py")
MEMORY_SPEC = importlib.util.spec_from_file_location(
    "bima_failure_memory_benchmark_runtime", MEMORY_SCRIPT)
if MEMORY_SPEC is None or MEMORY_SPEC.loader is None:
    raise RuntimeError("cannot load the reviewed failure-memory implementation")
failure_memory = importlib.util.module_from_spec(MEMORY_SPEC)
MEMORY_SPEC.loader.exec_module(failure_memory)
failure_records = failure_memory.failure_records

CONTRACT_SCRIPT = Path(__file__).resolve().with_name("benchmark_contract.py")
CONTRACT_SPEC = importlib.util.spec_from_file_location(
    "bima_failure_memory_benchmark_contract", CONTRACT_SCRIPT)
if CONTRACT_SPEC is None or CONTRACT_SPEC.loader is None:
    raise RuntimeError("cannot load the reviewed benchmark contract")
benchmark_contract = importlib.util.module_from_spec(CONTRACT_SPEC)
CONTRACT_SPEC.loader.exec_module(benchmark_contract)

BenchmarkError = benchmark_contract.BenchmarkError
strict_json = benchmark_contract.strict_json
load_document = benchmark_contract.load_document
canonical_bytes = benchmark_contract.canonical_bytes
_exact = benchmark_contract.validate_exact_fields
_string = benchmark_contract.validate_string
_identifier = benchmark_contract.validate_identifier
_sha256 = benchmark_contract.validate_sha256
_ppm = benchmark_contract.validate_ppm
_sorted_ids = benchmark_contract.validate_sorted_ids


MAX_QUERIES = 1000
MINIMUM_QUERIES = 10
REQUEST_FIELDS = {
    "schema", "benchmark_id", "dataset_id", "record_set_sha256",
    "held_out", "acceptance", "queries",
}


def validate_request(value):
    _exact(value, REQUEST_FIELDS, "benchmark request")
    if value["schema"] != "bima-failure-memory-benchmark-request.v1":
        raise BenchmarkError("unsupported benchmark request schema")
    _identifier(value["benchmark_id"], "benchmark_id")
    _identifier(value["dataset_id"], "dataset_id")
    _sha256(value["record_set_sha256"], "record_set_sha256")
    if type(value["held_out"]) is not bool:
        raise BenchmarkError("held_out must be boolean")

    _exact(value["acceptance"], {
        "k", "minimum_recall_ppm", "minimum_mrr_ppm",
        "maximum_false_match_ppm", "maximum_stale_hit_ppm",
    }, "benchmark acceptance")
    if type(value["acceptance"]["k"]) is not int or not 1 <= value["acceptance"]["k"] <= 50:
        raise BenchmarkError("acceptance k is outside 1 to 50")
    for field in (
            "minimum_recall_ppm", "minimum_mrr_ppm",
            "maximum_false_match_ppm", "maximum_stale_hit_ppm"):
        _ppm(value["acceptance"][field], field)

    queries = value["queries"]
    if not isinstance(queries, list) or len(queries) > MAX_QUERIES:
        raise BenchmarkError("queries are outside their item bounds")
    query_ids = []
    for query in queries:
        _exact(query, {
            "id", "text", "project_id", "relevant_record_ids",
            "forbidden_record_ids",
        }, "benchmark query")
        _identifier(query["id"], "query id")
        _string(query["text"], "query text")
        _identifier(query["project_id"], "query project_id")
        _sorted_ids(query["relevant_record_ids"], "relevant record IDs", 1)
        _sorted_ids(query["forbidden_record_ids"], "forbidden record IDs")
        if set(query["relevant_record_ids"]) & set(query["forbidden_record_ids"]):
            raise BenchmarkError("relevant and forbidden record IDs overlap")
        query_ids.append(query["id"])
    if query_ids != sorted(set(query_ids)):
        raise BenchmarkError("query IDs must be unique and sorted")
    return value


def bind_record_set(record_set, request):
    """Return a validated request bound to the actual record-set digest."""
    validate_request(request)
    summary = failure_records.summarize(record_set)
    if request["dataset_id"] != summary["dataset_id"]:
        raise BenchmarkError("benchmark dataset_id does not match the record set")
    bound = dict(request)
    bound["record_set_sha256"] = summary["record_set_sha256"]
    return bound


def _ppm_fraction(value):
    return (value.numerator * 1_000_000) // value.denominator if value else 0


def _blocked(request, record_summary, reason_code):
    return {
        "schema": "bima-failure-memory-benchmark-report.v1",
        "benchmark_id": request["benchmark_id"],
        "dataset_id": request["dataset_id"],
        "record_set_sha256": record_summary["record_set_sha256"],
        "request_sha256": benchmark_contract.digest(request),
        "status": "BLOCKED",
        "reason_code": reason_code,
        "real_verified_records": record_summary["real_verified_records"],
        "query_count": len(request["queries"]),
        "k": request["acceptance"]["k"],
        "metrics": None,
        "database_created": False,
    }


def benchmark(record_set, request, database_path, repository_root):
    failure_records.validate_record_set(record_set)
    validate_request(request)
    summary = failure_records.summarize(record_set)
    if request["dataset_id"] != record_set["dataset_id"]:
        raise BenchmarkError("benchmark dataset_id does not match the record set")
    if request["record_set_sha256"] != summary["record_set_sha256"]:
        raise BenchmarkError("benchmark record-set digest does not match")
    if summary["real_verified_records"] < failure_memory.MINIMUM_REAL_CASES:
        return _blocked(request, summary, "INSUFFICIENT_REAL_CASES")
    if not request["held_out"]:
        return _blocked(request, summary, "HELD_OUT_QUERIES_REQUIRED")
    if len(request["queries"]) < MINIMUM_QUERIES:
        return _blocked(request, summary, "INSUFFICIENT_HELD_OUT_QUERIES")

    records_by_id = {record["id"]: record for record in record_set["records"]}
    for query in request["queries"]:
        for record_id in query["relevant_record_ids"]:
            record = records_by_id.get(record_id)
            if record is None or record["status"] != "ACTIVE":
                raise BenchmarkError("relevant records must exist and be active")
        for record_id in query["forbidden_record_ids"]:
            if record_id not in records_by_id:
                raise BenchmarkError("forbidden records must exist in the source set")

    build = failure_memory.build_index(record_set, database_path, repository_root)
    k = request["acceptance"]["k"]
    inactive_record_ids = {
        record["id"] for record in record_set["records"]
        if record["status"] != "ACTIVE"
    }
    relevant_found = 0
    relevant_total = 0
    reciprocal_rank_total = Fraction(0, 1)
    false_matches = 0
    returned_total = 0
    stale_hits = 0
    query_results = []
    for query in request["queries"]:
        results = failure_memory.search(
            database_path, query["text"], query["project_id"], limit=k)
        returned_ids = [item["record_id"] for item in results]
        relevant = set(query["relevant_record_ids"])
        forbidden = set(query["forbidden_record_ids"]) | inactive_record_ids
        found = relevant & set(returned_ids)
        relevant_found += len(found)
        relevant_total += len(relevant)
        returned_total += len(returned_ids)
        false_matches += sum(record_id not in relevant for record_id in returned_ids)
        stale_hits += sum(record_id in forbidden for record_id in returned_ids)
        first_rank = next(
            (index for index, record_id in enumerate(returned_ids, 1)
             if record_id in relevant), None)
        if first_rank is not None:
            reciprocal_rank_total += Fraction(1, first_rank)
        query_results.append({
            "id": query["id"],
            "returned_record_ids": returned_ids,
            "first_relevant_rank": first_rank,
        })

    metrics = {
        "recall_at_k_ppm": _ppm_fraction(Fraction(relevant_found, relevant_total)),
        "mrr_ppm": _ppm_fraction(
            reciprocal_rank_total / len(request["queries"])),
        "false_match_ppm": _ppm_fraction(
            Fraction(false_matches, returned_total)) if returned_total else 0,
        "stale_hit_ppm": _ppm_fraction(
            Fraction(stale_hits, returned_total)) if returned_total else 0,
    }
    acceptance = request["acceptance"]
    passed = (
        metrics["recall_at_k_ppm"] >= acceptance["minimum_recall_ppm"]
        and metrics["mrr_ppm"] >= acceptance["minimum_mrr_ppm"]
        and metrics["false_match_ppm"] <= acceptance["maximum_false_match_ppm"]
        and metrics["stale_hit_ppm"] <= acceptance["maximum_stale_hit_ppm"]
    )
    return {
        "schema": "bima-failure-memory-benchmark-report.v1",
        "benchmark_id": request["benchmark_id"],
        "dataset_id": request["dataset_id"],
        "record_set_sha256": summary["record_set_sha256"],
        "request_sha256": benchmark_contract.digest(request),
        "status": "PASS" if passed else "FAIL",
        "reason_code": "ACCEPTANCE_SATISFIED" if passed else "ACCEPTANCE_NOT_SATISFIED",
        "real_verified_records": summary["real_verified_records"],
        "query_count": len(request["queries"]),
        "k": k,
        "metrics": metrics,
        "database_created": build["database_created"],
        "queries": query_results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--bind-record-set", action="store_true",
        help="bind the request to the canonical digest of --records at invocation time")
    args = parser.parse_args()
    try:
        record_set = failure_records.validate_record_set(
            failure_records.load_document(args.records))
        request = validate_request(load_document(args.queries))
        if args.bind_record_set:
            request = bind_record_set(record_set, request)
        report = benchmark(record_set, request, args.database, args.repository_root)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_bytes(canonical_bytes(report))
        print(
            f"failure-memory-benchmark: {report['status']}; "
            f"reason={report['reason_code']}; queries={report['query_count']}")
        return {"PASS": 0, "FAIL": 1, "BLOCKED": 3}[report["status"]]
    except (BenchmarkError, failure_records.FailureRecordError,
            failure_memory.FailureMemoryError, OSError, sqlite3.Error) as exc:
        print(f"failure-memory-benchmark: ERROR; {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
