"""Compare deterministic repository-audit evidence fields."""

import argparse
import json
from pathlib import Path


FIELDS = (
    "schema_version",
    "module",
    "status",
    "validator_sha256",
    "python_version",
    "revision",
    "dirty",
    "policy_sha256",
    "files_checked",
    "local_links_checked",
    "findings",
)


def comparable(result: dict) -> dict:
    return {field: result.get(field) for field in FIELDS}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        left = comparable(json.loads(args.left.read_text(encoding="utf-8")))
        right = comparable(json.loads(args.right.read_text(encoding="utf-8")))
        matches = left == right
        comparison = {
            "schema_version": 1,
            "module": "repository-audit-parity",
            "status": "pass" if matches else "fail",
            "compared_fields": list(FIELDS),
            "differences": {
                field: {"left": left[field], "right": right[field]}
                for field in FIELDS
                if left[field] != right[field]
            },
        }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        comparison = {
            "schema_version": 1,
            "module": "repository-audit-parity",
            "status": "error",
            "compared_fields": list(FIELDS),
            "differences": {},
            "error": type(exc).__name__,
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(comparison, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"repository-audit-parity: {comparison['status']}")
    return {"pass": 0, "fail": 1, "error": 2}[comparison["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
