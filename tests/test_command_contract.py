import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKFILE = ROOT / "Taskfile.yml"
README = ROOT / "README.md"
CONTRACT = ROOT / "docs" / "standards" / "COMMAND-CONTRACT.md"

TASK_NAME = re.compile(r"^  ([a-z0-9-]+):$", re.MULTILINE)
README_COMMAND = re.compile(r"^task ([a-z0-9-]+)", re.MULTILINE)
CONTRACT_ROW = re.compile(r"^\| `task ([a-z0-9-]+)`", re.MULTILINE)
FENCE = re.compile(r"^```text\n(.*?)^```$", re.MULTILINE | re.DOTALL)


def task_names():
    names = set(TASK_NAME.findall(TASKFILE.read_text(encoding="utf-8")))
    return names - {"default"}


def readme_names():
    names = set()
    for block in FENCE.findall(README.read_text(encoding="utf-8")):
        names.update(README_COMMAND.findall(block))
    return names


def contract_names():
    return set(CONTRACT_ROW.findall(CONTRACT.read_text(encoding="utf-8")))


class CommandContractTests(unittest.TestCase):
    def test_taskfile_declares_the_expected_command_set(self):
        self.assertEqual(len(task_names()), 22, sorted(task_names()))

    def test_readme_and_contract_match_the_taskfile(self):
        declared = task_names()
        for label, names in (("README", readme_names()),
                             ("COMMAND-CONTRACT", contract_names())):
            self.assertEqual(
                names, declared,
                f"{label} drift: missing={sorted(declared - names)} "
                f"extra={sorted(names - declared)}")

    def test_readme_commands_live_in_one_text_fence(self):
        blocks = FENCE.findall(README.read_text(encoding="utf-8"))
        with_commands = [block for block in blocks
                         if README_COMMAND.search(block)]
        self.assertEqual(len(with_commands), 1, len(blocks))


if __name__ == "__main__":
    unittest.main()
