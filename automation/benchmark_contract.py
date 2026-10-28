"""Deterministic, dependency-free mechanics shared by benchmark adapters."""

import hashlib
import json
from pathlib import Path
import re


MAX_INPUT_BYTES = 4 * 1024 * 1024
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class BenchmarkError(ValueError):
    """Benchmark input or execution violates its deterministic contract."""


def validate_exact_fields(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise BenchmarkError(f"{label} fields do not match the v1 contract")


def validate_string(value, label, maximum=512):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise BenchmarkError(f"{label} is invalid")


def validate_identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise BenchmarkError(f"{label} is invalid")


def validate_sha256(value, label):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise BenchmarkError(f"{label} is invalid")


def validate_ppm(value, label):
    if type(value) is not int or not 0 <= value <= 1_000_000:
        raise BenchmarkError(f"{label} must be integer parts-per-million")


def validate_sorted_ids(value, label, minimum=0):
    if not isinstance(value, list) or not minimum <= len(value) <= 100:
        raise BenchmarkError(f"{label} is outside its item bounds")
    for item in value:
        validate_identifier(item, label)
    if value != sorted(set(value)):
        raise BenchmarkError(f"{label} must be unique and sorted")


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise BenchmarkError("duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise BenchmarkError("non-finite JSON number")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise BenchmarkError("input is not strict UTF-8 JSON") from exc


def load_document(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise BenchmarkError("input must be a regular file within the byte limit")
    return strict_json(path.read_bytes())


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
