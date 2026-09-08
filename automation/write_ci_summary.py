"""Create a small machine-readable manifest for Dagger CI evidence."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


COMPONENTS = {
    "audit": "audit.exit-code",
    "tests": "tests.exit-code",
    "workflow_lint": "actionlint.exit-code",
}


def create_summary(evidence: Path) -> dict:
    components = {}
    for name, relative_path in COMPONENTS.items():
        path = evidence / relative_path
        try:
            exit_code = int(path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            exit_code = None
        components[name] = {
            "exit_code": exit_code,
            "status": "pass" if exit_code == 0 else "error" if exit_code is None else "fail",
        }

    statuses = {item["status"] for item in components.values()}
    status = "error" if "error" in statuses else "fail" if "fail" in statuses else "pass"
    return {
        "schema_version": 1,
        "module": "bima-infra-ci",
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "components": components,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    summary = create_summary(args.evidence)
    args.evidence.mkdir(parents=True, exist_ok=True)
    (args.evidence / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(f"bima-infra-ci: {summary['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
