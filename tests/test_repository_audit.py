import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "automation" / "repository_audit.py"
SPEC = importlib.util.spec_from_file_location("repository_audit", SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class RepositoryAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "subject"
        self.root.mkdir()
        self.git("init", "-q")
        self.put("README.md", "# Example\n\n[Guide](docs/guide.md)\n")
        self.put("AGENTS.md", "# Instructions\n")
        self.put("docs/guide.md", "# Guide\n\n[Home](../README.md)\n")
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")

    def git(self, *args):
        return audit.git(self.root, *args)

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def codes(self, result=None):
        return {x["code"] for x in (result or audit.audit(self.root))["findings"]}

    def test_clean_repository_has_revision_and_real_counts(self):
        result = audit.audit(self.root)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["files_checked"], 3)
        self.assertEqual(result["local_links_checked"], 2)
        self.assertEqual(len(result["revision"]), 40)
        self.assertFalse(result["dirty"])

    def test_missing_required_file_fails(self):
        (self.root / "AGENTS.md").unlink()
        self.assertIn("required-file", self.codes())

    def test_empty_required_file_fails(self):
        self.put("AGENTS.md", "")
        self.assertIn("required-file", self.codes())

    def test_broken_link_fails_with_line_number(self):
        self.put("README.md", "# Example\n\n[Missing](absent.md)\n")
        result = audit.audit(self.root)
        broken = next(x for x in result["findings"] if x["code"] == "broken-link")
        self.assertEqual(broken["line"], 3)
        self.assertTrue(result["dirty"])

    def test_code_examples_and_external_links_are_not_fetched(self):
        self.put("README.md", '# Demo\n```md\n[x](missing.md)\n```\n'
                 '~~~\n[x](missing.md)\n~~~\n`[x](missing.md)`\n'
                 '    [x](missing.md)\n[x](https://example.invalid)\n[x](#heading)\n')
        self.assertEqual(audit.audit(self.root)["status"], "pass")

    def test_encoded_space_image_root_and_parent_links(self):
        self.put("docs/a b.md", "# Space\n")
        self.put("README.md", '[x](docs/a%20b.md)\n![x](<docs/a b.md>)\n[x](/AGENTS.md)\n')
        self.assertEqual(audit.audit(self.root)["status"], "pass")

    def test_link_cannot_leave_repository(self):
        self.put("README.md", "[secret](../outside.md)\n[secret](%2e%2e/outside.md)\n")
        self.assertIn("unsafe-link", self.codes())

    def test_ignored_file_cannot_satisfy_link(self):
        self.put(".gitignore", "ignored.md\n")
        self.put("ignored.md", "# Ignored\n")
        self.put("README.md", "[x](ignored.md)\n")
        self.assertIn("broken-link", self.codes())

    def test_untracked_input_is_checked_but_ignored_output_is_not(self):
        self.put("new.json", "broken")
        self.put(".gitignore", ".artifacts/\n")
        self.put(".artifacts/old.json", "broken")
        invalid = [x["path"] for x in audit.audit(self.root)["findings"] if x["code"] == "invalid-json"]
        self.assertEqual(invalid, ["new.json"])

    def test_invalid_duplicate_and_nonfinite_json_fail_without_content_leak(self):
        for content in ('{"secret":}', '{"a":1,"a":2}', '{"a":NaN}'):
            with self.subTest(content=content):
                self.put("data.json", content)
                result = audit.audit(self.root)
                self.assertIn("invalid-json", self.codes(result))
                self.assertNotIn("secret", json.dumps(result))

    def test_file_budget_blocks_large_file(self):
        self.put("data.bin", "x" * (audit.DEFAULT_POLICY["max_file_bytes"] + 1))
        self.assertIn("file-size", self.codes())

    def test_valid_policy_is_hashed(self):
        self.put("policy.json", json.dumps(audit.DEFAULT_POLICY))
        result = audit.audit(self.root, "policy.json")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(len(result["policy_sha256"]), 64)
        self.assertEqual(len(result["validator_sha256"]), 64)

    def test_deep_json_does_not_abort_audit(self):
        self.put("deep.json", "[" * 2000 + "0" + "]" * 2000)
        result = audit.audit(self.root)
        self.assertIn(result["status"], {"pass", "fail"})
        if result["status"] == "fail":
            self.assertIn("invalid-json", self.codes(result))
        self.assertEqual(audit.audit(self.root, "deep.json")["status"], "error")
        with patch.object(audit, "strict_json", side_effect=RecursionError):
            self.assertIn("invalid-json", self.codes())

    def test_caller_python_modules_are_not_imported(self):
        self.put("json.py", "raise RuntimeError('caller code executed')\n")
        self.put("sitecustomize.py", "raise RuntimeError('caller code executed')\n")
        output = Path(self.temp.name) / "isolated-output"
        run = subprocess.run([sys.executable, "-I", str(SCRIPT), "--root", str(self.root),
                              "--output", str(output)], cwd=self.root,
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertNotIn("caller code executed", run.stderr)

    def test_report_escapes_markup_in_filenames(self):
        result = audit.audit(self.root)
        result["findings"] = [{"code": "broken-link", "path": "<img src=x onerror=alert(1)>",
                               "line": 1, "message": "example"}]
        output = Path(self.temp.name) / "escaped-output"
        audit.write_report(result, output)
        report = (output / "report.md").read_text(encoding="utf-8")
        self.assertNotIn("<img", report)
        self.assertIn("&lt;img", report)

    def test_malformed_policy_fails_closed(self):
        bad_policies = [[], {}, {**audit.DEFAULT_POLICY, "unknown": 1},
                        {**audit.DEFAULT_POLICY, "schema_version": True},
                        {**audit.DEFAULT_POLICY, "required_files": []},
                        {**audit.DEFAULT_POLICY, "required_files": ["../secret"]},
                        {**audit.DEFAULT_POLICY, "required_files": [".git/config"]},
                        {**audit.DEFAULT_POLICY, "required_files": ["C:/secret"]},
                        {**audit.DEFAULT_POLICY, "max_file_bytes": True},
                        {**audit.DEFAULT_POLICY, "max_file_bytes": -1}]
        for policy in bad_policies:
            with self.subTest(policy=policy):
                self.put("policy.json", json.dumps(policy))
                self.assertEqual(audit.audit(self.root, "policy.json")["status"], "error")
        self.assertEqual(audit.audit(self.root, "absent.json")["status"], "error")

    def test_non_git_and_nested_root_are_errors(self):
        self.assertEqual(audit.audit(Path(self.temp.name))["status"], "error")
        self.assertEqual(audit.audit(self.root / "docs")["status"], "error")

    def test_symlink_is_rejected_without_reading_target(self):
        outside = Path(self.temp.name) / "secret.json"
        outside.write_text("DO NOT READ", encoding="utf-8")
        try:
            (self.root / "escape.json").symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"OS does not permit symlink creation: {exc}")
        result = audit.audit(self.root)
        self.assertIn("unreadable-file", self.codes(result))
        self.assertNotIn("DO NOT READ", json.dumps(result))

    def test_cli_exit_codes_and_evidence_for_pass_fail_error(self):
        for expected, policy in [(0, None), (1, None), (2, "absent.json")]:
            with self.subTest(expected=expected):
                if expected == 1:
                    self.put("README.md", "[broken](absent.md)\n")
                output = Path(self.temp.name) / f"output-{expected}"
                args = [sys.executable, "-I", str(SCRIPT), "--root", str(self.root), "--output", str(output)]
                if policy:
                    args += ["--policy", policy]
                run = subprocess.run(args, capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, expected, run.stderr)
                result = json.loads((output / "result.json").read_text(encoding="utf-8"))
                self.assertEqual(result["status"], ["pass", "fail", "error"][expected])
                self.assertIn(f"**{result['status']}**", (output / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
