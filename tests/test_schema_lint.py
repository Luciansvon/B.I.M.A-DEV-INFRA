import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "schema_lint.py"


def run(root):
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--root", str(root)],
        cwd=ROOT, capture_output=True, text=True)


def write_schema(root, document):
    path = root / "schemas" / "sample.schema.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return path


def valid_schema():
    return {
        "type": "object",
        "required": ["schema", "items"],
        "additionalProperties": False,
        "properties": {
            "schema": {"const": "sample.v1"},
            "items": {"type": "array", "items": {"$ref": "#/$defs/item"}},
        },
        "$defs": {
            "item": {
                "type": "object",
                "required": ["id"],
                "additionalProperties": False,
                "properties": {"id": {"type": "string", "pattern": "^[a-z]+$"}},
            },
        },
    }


class SchemaLintTests(unittest.TestCase):
    def test_valid_fixture_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_schema(root, valid_schema())
            result = run(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("schema-lint: pass; schemas=1", result.stdout)

    def test_required_name_missing_from_properties_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = valid_schema()
            document["required"].append("absent")
            write_schema(root, document)
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("required name is not in properties: absent", result.stderr)

    def test_duplicate_required_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = valid_schema()
            document["required"].append("schema")
            write_schema(root, document)
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("duplicate required name", result.stderr)

    def test_broken_local_ref_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = valid_schema()
            document["properties"]["items"]["items"] = {"$ref": "#/$defs/absent"}
            write_schema(root, document)
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unresolved local $ref: #/$defs/absent", result.stderr)

    def test_invalid_pattern_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = valid_schema()
            document["properties"]["schema"] = {"type": "string", "pattern": "^([a-z]+$"}
            write_schema(root, document)
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid pattern", result.stderr)

    def test_unreferenced_defs_entry_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = valid_schema()
            document["$defs"]["unused"] = {"type": "string"}
            write_schema(root, document)
            result = run(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("$defs entry is never referenced: unused", result.stderr)


if __name__ == "__main__":
    unittest.main()
