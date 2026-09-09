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
SCRIPT = ROOT / "automation" / "agent_packet.py"
SPEC = importlib.util.spec_from_file_location("agent_packet", SCRIPT)
packets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packets)


def sample_canonical(status="pass", findings=None):
    findings = [] if findings is None else findings
    return {
        "checks": [{
            "findings": findings,
            "id": "repository-audit",
            "metrics": {
                "files_checked": 3,
                "findings_count": len(findings),
                "local_links_checked": 2,
            },
            "status": status,
        }],
        "policy": {"sha256": "c" * 64},
        "schema": "bima-evidence.v1",
        "status": status,
        "subject": {"dirty": False, "revision": "b" * 40},
        "toolchain": [
            {"name": "canonical-evidence", "sha256": "d" * 64},
            {"name": "python", "version": "3.13.15"},
            {"name": "repository-audit", "sha256": "a" * 64},
        ],
    }


def finding(number=1, **overrides):
    value = {
        "code": f"broken-link-{number}",
        "path": f"docs/file-{number}.md",
        "line": number,
        "message": f"missing local target {number}",
    }
    value.update(overrides)
    return value


class AgentPacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write_canonical(self, name, value, *, canonical=True):
        path = self.root / name
        if canonical:
            path.write_bytes(packets.json_bytes(value))
        else:
            path.write_text(json.dumps(value, indent=4) + "\n", encoding="utf-8")
        return path

    def test_pass_removes_stale_outputs_and_emits_no_packet(self):
        source = self.write_canonical("pass.json", sample_canonical())
        output = self.root / "agent"
        output.mkdir()
        for name in packets.OWNED_OUTPUTS:
            (output / name).write_text("stale", encoding="utf-8")
        status, digest = packets.generate(source, output)
        self.assertEqual((status, digest), ("pass", None))
        self.assertFalse(any((output / name).exists() for name in packets.OWNED_OUTPUTS))

    def test_fail_routes_known_findings_to_machine(self):
        source = self.write_canonical(
            "fail.json", sample_canonical("fail", [finding()]))
        output = self.root / "agent"
        status, digest = packets.generate(source, output)
        packet = json.loads((output / "packet.json").read_text(encoding="utf-8"))
        self.assertEqual(status, "fail")
        self.assertEqual(packet["route"], "machine")
        self.assertEqual(packet["routing_reason"], "known-deterministic-findings")
        self.assertEqual(packet["artifact_hash"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(packet["affected_paths"], ["docs/file-1.md"])
        self.assertEqual(packet["error_codes"], ["broken-link-1"])
        self.assertEqual(packet["retries"], 0)
        self.assertIsNone(packet["repeatable"])
        self.assertEqual((output / "packet.sha256").read_text(encoding="ascii"),
                         f"{digest}  packet.json\n")

    def test_error_routes_unclassified_failure_to_agent(self):
        canonical = sample_canonical("error", [finding(code="audit-error")])
        canonical["subject"] = {"dirty": None, "revision": None}
        source = self.write_canonical("error.json", canonical)
        output = self.root / "agent"
        status, _ = packets.generate(source, output)
        packet = json.loads((output / "packet.json").read_text(encoding="utf-8"))
        self.assertEqual(status, "error")
        self.assertEqual(packet["route"], "agent")
        self.assertEqual(packet["routing_reason"], "unclassified-audit-error")
        self.assertIsNone(packet["commit"])
        self.assertIsNone(packet["dirty"])

    def test_packet_bytes_and_hash_are_deterministic(self):
        canonical = sample_canonical("fail", [finding(1), finding(2)])
        source = self.write_canonical("fail.json", canonical)
        first = self.root / "first"
        second = self.root / "second"
        _, first_digest = packets.generate(source, first)
        _, second_digest = packets.generate(source, second)
        self.assertEqual(first_digest, second_digest)
        self.assertEqual((first / "packet.json").read_bytes(),
                         (second / "packet.json").read_bytes())
        self.assertTrue((first / "packet.json").read_bytes().endswith(b"\n"))
        self.assertNotIn(b"\r\n", (first / "packet.json").read_bytes())

    def test_packet_is_bounded_and_reports_truncation(self):
        findings = [finding(index, code="c" * 70, path=f"{index}-" + "p" * 520,
                            message="m" * 600) for index in range(1, 23)]
        findings.sort(key=lambda item: (item["code"], item["path"], item["line"],
                                        item["message"]))
        source = self.write_canonical("many.json", sample_canonical("fail", findings))
        output = self.root / "agent"
        packets.generate(source, output)
        packet = json.loads((output / "packet.json").read_text(encoding="utf-8"))
        self.assertEqual(packet["total_findings"], 22)
        self.assertEqual(len(packet["relevant_evidence"]), 20)
        self.assertEqual(len(packet["affected_paths"]), 20)
        self.assertLessEqual(len(packet["relevant_evidence"][0]["code"]), 64)
        self.assertLessEqual(len(packet["relevant_evidence"][0]["path"]), 512)
        self.assertLessEqual(len(packet["relevant_evidence"][0]["message"]), 512)
        self.assertTrue(packet["evidence_truncated"])

    def test_rejects_noncanonical_duplicate_nonfinite_and_inconsistent_input(self):
        inconsistent = sample_canonical()
        inconsistent["checks"][0]["metrics"]["findings_count"] = 1
        wrong_toolchain = sample_canonical()
        wrong_toolchain["toolchain"] = list(reversed(wrong_toolchain["toolchain"]))
        unsorted = sample_canonical("fail", [finding(2), finding(1)])
        cases = {
            "formatted": json.dumps(sample_canonical(), indent=4) + "\n",
            "duplicate": packets.json_bytes(sample_canonical()).decode().rstrip()[:-1]
                         + ', "status": "pass"}\n',
            "nonfinite": packets.json_bytes(sample_canonical()).decode().replace(
                '"files_checked": 3', '"files_checked": NaN'),
            "inconsistent": packets.json_bytes(inconsistent).decode(),
            "wrong-toolchain": packets.json_bytes(wrong_toolchain).decode(),
            "unsorted": packets.json_bytes(unsorted).decode(),
        }
        for name, text in cases.items():
            with self.subTest(name=name):
                path = self.root / f"{name}.json"
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    packets.generate(path, self.root / f"out-{name}")

    def test_cli_exit_codes_are_sanitized_and_nonpass_does_not_fail_generation(self):
        source = self.write_canonical(
            "fail.json", sample_canonical("fail", [finding()]))
        run = subprocess.run([sys.executable, "-I", str(SCRIPT), "--input", str(source),
                              "--output", str(self.root / "agent")], capture_output=True,
                             text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("status=fail; route=machine", run.stdout)
        invalid = self.root / "invalid.json"
        invalid.write_text('{"secret":"DO NOT LEAK"}', encoding="utf-8")
        run = subprocess.run([sys.executable, "-I", str(SCRIPT), "--input", str(invalid),
                              "--output", str(self.root / "invalid-output")],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 2)
        self.assertNotIn("DO NOT LEAK", run.stderr)

    def test_packet_excludes_runtime_prompt_and_raw_log_fields(self):
        canonical = copy.deepcopy(sample_canonical("fail", [finding()]))
        source = self.write_canonical("fail.json", canonical)
        output = self.root / "agent"
        packets.generate(source, output)
        packet = json.loads((output / "packet.json").read_text(encoding="utf-8"))
        serialized = json.dumps(packet)
        for forbidden in ("generated_at", "runtime", "raw_log", "prompt", "instructions"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
