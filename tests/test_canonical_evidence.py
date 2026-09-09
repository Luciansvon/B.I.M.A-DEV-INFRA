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
SCRIPT = ROOT / "automation" / "canonical_evidence.py"
SPEC = importlib.util.spec_from_file_location("canonical_evidence", SCRIPT)
evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence)


def sample_result():
    return {
        "schema_version": 1,
        "module": "repository-audit",
        "status": "pass",
        "generated_at": "2026-09-09T00:00:00+00:00",
        "validator_sha256": "a" * 64,
        "python_version": "3.13.15",
        "revision": "b" * 40,
        "dirty": False,
        "policy_sha256": "c" * 64,
        "files_checked": 3,
        "local_links_checked": 2,
        "findings": [],
    }


class CanonicalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write_source(self, name, value, *, reverse=False, crlf=False):
        path = self.root / name
        if reverse:
            value = dict(reversed(list(value.items())))
        text = json.dumps(value, indent=4)
        if crlf:
            text = text.replace("\n", "\r\n")
        path.write_bytes((text + ("\r\n" if crlf else "\n")).encode("utf-8"))
        return path

    def test_volatile_source_and_formatting_do_not_change_canonical_bytes(self):
        first = sample_result()
        second = copy.deepcopy(first)
        second["generated_at"] = "2026-09-09T01:02:03+00:00"
        one = self.write_source("one.json", first)
        two = self.write_source("two.json", second, reverse=True, crlf=True)
        first_output = self.root / "first"
        second_output = self.root / "second"
        first_digest = evidence.generate(one, first_output)
        second_digest = evidence.generate(two, second_output)
        self.assertEqual(first_digest, second_digest)
        self.assertEqual((first_output / "canonical.json").read_bytes(),
                         (second_output / "canonical.json").read_bytes())
        self.assertNotEqual(json.loads((first_output / "execution.json").read_text())["source"]["sha256"],
                            json.loads((second_output / "execution.json").read_text())["source"]["sha256"])

    def test_findings_are_sorted_and_failure_is_preserved(self):
        source = sample_result()
        source["status"] = "fail"
        source["findings"] = [
            {"code": "z-last", "path": "b", "line": None, "message": "last"},
            {"code": "a-first", "path": "a", "line": 2, "message": "first"},
        ]
        canonical = evidence.canonicalize(source)
        self.assertEqual(canonical["status"], "fail")
        self.assertEqual(canonical["checks"][0]["metrics"]["findings_count"], 2)
        self.assertEqual([item["code"] for item in canonical["checks"][0]["findings"]],
                         ["a-first", "z-last"])

    def test_rejects_malformed_source_contracts(self):
        invalid = []
        for key, value in [
                ("schema_version", True), ("module", "other"), ("status", "unknown"),
                ("validator_sha256", "bad"), ("revision", "bad"),
                ("dirty", 1), ("files_checked", True), ("findings", {})]:
            item = sample_result()
            item[key] = value
            invalid.append(item)
        extra = sample_result()
        extra["unexpected"] = True
        invalid.append(extra)
        failed_without_findings = sample_result()
        failed_without_findings["status"] = "fail"
        invalid.append(failed_without_findings)
        for item in invalid:
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    evidence.canonicalize(item)

    def test_rejects_duplicate_and_nonfinite_json(self):
        source = sample_result()
        text = json.dumps(source)
        duplicate = text[:-1] + ', "status": "pass"}'
        nonfinite = text.replace('"files_checked": 3', '"files_checked": NaN')
        for number, raw in enumerate((duplicate, nonfinite)):
            path = self.root / f"invalid-{number}.json"
            path.write_text(raw, encoding="utf-8")
            with self.assertRaises(ValueError):
                evidence.load_source(path)

    def test_hash_file_matches_lf_terminated_canonical_evidence(self):
        source = self.write_source("result.json", sample_result())
        output = self.root / "output"
        digest = evidence.generate(source, output)
        canonical_raw = (output / "canonical.json").read_bytes()
        self.assertTrue(canonical_raw.endswith(b"\n"))
        self.assertNotIn(b"\r\n", canonical_raw)
        self.assertEqual(digest, hashlib.sha256(canonical_raw).hexdigest())
        self.assertEqual((output / "canonical.sha256").read_text(encoding="ascii"),
                         f"{digest}  canonical.json\n")

    def test_execution_metadata_is_separate_from_canonical_result(self):
        source = self.write_source("result.json", sample_result())
        output = self.root / "output"
        digest = evidence.generate(source, output)
        canonical = json.loads((output / "canonical.json").read_text(encoding="utf-8"))
        execution = json.loads((output / "execution.json").read_text(encoding="utf-8"))
        self.assertNotIn("generated_at", canonical)
        self.assertNotIn("runtime", canonical)
        self.assertEqual(execution["canonical"]["sha256"], digest)
        self.assertEqual(execution["source"]["generated_at"], sample_result()["generated_at"])
        self.assertIn("system", execution["runtime"])

    def test_cli_normalizes_failure_without_masking_its_status(self):
        failed = sample_result()
        failed["status"] = "fail"
        failed["findings"] = [
            {"code": "broken-link", "path": "README.md", "line": 3,
             "message": "local link target is absent"}
        ]
        source = self.write_source("failed.json", failed)
        output = self.root / "failed-output"
        run = subprocess.run([sys.executable, "-I", str(SCRIPT), "--input", str(source),
                              "--output", str(output)], capture_output=True,
                             text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        canonical = json.loads((output / "canonical.json").read_text(encoding="utf-8"))
        self.assertEqual(canonical["status"], "fail")
        self.assertEqual(canonical["checks"][0]["status"], "fail")

    def test_cli_exit_codes_and_does_not_echo_invalid_content(self):
        valid = self.write_source("valid.json", sample_result())
        valid_output = self.root / "valid-output"
        run = subprocess.run([sys.executable, "-I", str(SCRIPT), "--input", str(valid),
                              "--output", str(valid_output)], capture_output=True,
                             text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("canonical-evidence: pass", run.stdout)
        invalid = self.root / "invalid.json"
        invalid.write_text('{"secret":"DO NOT LEAK"}', encoding="utf-8")
        invalid_output = self.root / "invalid-output"
        invalid_output.mkdir()
        for name in evidence.OWNED_OUTPUTS:
            (invalid_output / name).write_text("stale", encoding="utf-8")
        run = subprocess.run([sys.executable, "-I", str(SCRIPT), "--input", str(invalid),
                              "--output", str(invalid_output)],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 2)
        self.assertNotIn("DO NOT LEAK", run.stderr)
        self.assertFalse(any((invalid_output / name).exists() for name in evidence.OWNED_OUTPUTS))


if __name__ == "__main__":
    unittest.main()
