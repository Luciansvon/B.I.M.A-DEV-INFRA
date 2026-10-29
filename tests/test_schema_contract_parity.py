"""Keep checked-in JSON Schemas aligned with the hand-written validators.

No runtime code loads ``schemas/*.schema.json``, so drift is otherwise silent.
This test is intentionally stdlib-only: it checks the schema envelope, compares
each exported validator field-set constant with the schema it governs, and
documents every top-level set that exists only as an inline literal.
"""

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_SUFFIX = ".schema.json"

# schema file -> (module in automation/, exported field-set constant, schema path)
# An empty schema path means the document's top level.
FIELD_SET_PARITY = {
    # canonical_evidence.SOURCE_FIELDS describes the repository-audit input,
    # not the bima-evidence.v1 output; agent_packet owns the output shape.
    "bima-evidence.v1.schema.json": (
        ("agent_packet", "TOP_FIELDS", ()),
        ("agent_packet", "SUBJECT_FIELDS", ("properties", "subject")),
        ("agent_packet", "POLICY_FIELDS", ("properties", "policy")),
        ("agent_packet", "CHECK_FIELDS", ("properties", "checks", "items")),
        ("agent_packet", "METRIC_FIELDS",
         ("properties", "checks", "items", "properties", "metrics")),
        ("agent_packet", "FINDING_FIELDS",
         ("properties", "checks", "items", "properties", "findings", "items")),
    ),
    "bima-verification-result.v2.schema.json": (
        ("verification_result_contract", "RESULT_FIELDS", ()),
    ),
    "bima-artifact-manifest-request.v1.schema.json": (
        ("artifact_identity", "ARTIFACT_FIELDS", ("$defs", "artifact")),
    ),
    "bima-artifact-manifest.v1.schema.json": (
        ("artifact_identity", "MANIFEST_ARTIFACT_FIELDS", ("$defs", "artifact")),
    ),
    "bima-known-failure-registry.v1.schema.json": (
        ("known_failure_registry", "ENTRY_FIELDS", ("$defs", "entry")),
        ("known_failure_registry", "SCOPE_FIELDS", ("$defs", "scope")),
    ),
    "bima-failure-record-set.v1.schema.json": (
        ("failure_records", "RECORD_FIELDS", ("$defs", "record")),
    ),
    "bima-failure-memory-benchmark-request.v1.schema.json": (
        ("failure_memory_benchmark", "REQUEST_FIELDS", ()),
    ),
    "bima-normalization-config.v1.schema.json": (
        ("result_normalizer", "CONFIG_FIELDS", ()),
    ),
    "bima-release-evidence.v1.schema.json": (
        ("release_evidence", "EVIDENCE_FIELDS", ()),
        ("release_evidence", "ASSET_FIELDS", ("$defs", "asset")),
    ),
    "bima-trust-bundle.v1.schema.json": (
        ("trusted_policy_launcher", "BUNDLE_FIELDS", ()),
    ),
    "bima-workflow-catalog.v1.schema.json": (
        ("workflow_catalog", "TOP_KEYS", ()),
        ("workflow_catalog", "ENTRY_KEYS", ("$defs", "entry")),
    ),
    "bima-fleet.v1.schema.json": (
        ("fleet_dispatch", "TOP_KEYS", ()),
        ("fleet_dispatch", "ENTRY_KEYS", ("$defs", "entry")),
    ),
    "bima-fleet-evidence.v1.schema.json": (
        ("fleet_dispatch", "EVIDENCE_FIELDS", ()),
        ("fleet_dispatch", "DISPATCH_FIELDS", ("$defs", "dispatch")),
    ),
    "bima-dashboard-status.v1.schema.json": (
        ("dashboard", "TOP_KEYS", ()),
        ("dashboard", "RUN_KEYS", ("$defs", "run")),
    ),
}

# Top-level field sets that no validator exports as a constant. Each entry
# names the function that owns the inline set so the gap is visible and stale
# exceptions are caught when a schema or validator is renamed.
EXPLICIT_EXCEPTIONS = {
    ("bima-agent-packet.v1.schema.json", ()):
        "agent_packet.build_packet assembles the output fields inline; "
        "TOP_FIELDS validates its bima-evidence input instead.",
    ("bima-artifact-manifest-request.v1.schema.json", ()):
        "artifact_identity.validate_request inlines the top-level set; "
        "ARTIFACT_FIELDS covers only $defs/artifact (mapped).",
    ("bima-artifact-manifest.v1.schema.json", ()):
        "artifact_identity.validate_manifest inlines the top-level set; "
        "MANIFEST_ARTIFACT_FIELDS covers only $defs/artifact (mapped).",
    ("bima-artifact-verification.v1.schema.json", ()):
        "artifact_identity.verify_manifest assembles the report fields inline; "
        "no exported field-set constant exists.",
    ("bima-decision.v1.schema.json", ()):
        "policy_gate.validate_decision inlines the top-level set; "
        "no exported field-set constant exists.",
    ("bima-evidence.execution.v1.schema.json", ()):
        "canonical_evidence.generate assembles the execution document inline; "
        "no exported field-set constant exists.",
    ("bima-experiment-decision.v1.schema.json", ()):
        "experiment_gate.evaluate assembles the decision inline; "
        "no exported field-set constant exists.",
    ("bima-experiment-request.v1.schema.json", ()):
        "experiment_gate.validate_request inlines the top-level set; "
        "no exported field-set constant exists.",
    ("bima-failure-memory-benchmark-report.v1.schema.json", ()):
        "failure_memory_benchmark._blocked and benchmark assemble the report "
        "inline; queries is optional so blocked reports can omit it.",
    ("bima-failure-memory-report.v1.schema.json", ()):
        "failure_memory.readiness assembles the report inline; "
        "no exported field-set constant exists.",
    ("bima-failure-record-set.v1.schema.json", ()):
        "failure_records.validate_record_set inlines the top-level set; "
        "RECORD_FIELDS covers each $defs/record (mapped).",
    ("bima-known-failure-classification.v1.schema.json", ()):
        "known_failure_registry.classify assembles the classification inline; "
        "no exported field-set constant exists.",
    ("bima-known-failure-registry.v1.schema.json", ()):
        "known_failure_registry.validate_registry inlines the top-level set; "
        "ENTRY_FIELDS and SCOPE_FIELDS cover $defs/entry and $defs/scope (mapped).",
    ("bima-normalization-request.v1.schema.json", ()):
        "result_normalizer.validate_request inlines the top-level set; "
        "CONFIG_FIELDS belongs to the separate config schema.",
    ("bima-operation-request.v1.schema.json", ()):
        "policy_gate.validate_request inlines the top-level set; "
        "no exported field-set constant exists.",
    ("bima-policy.v1.schema.json", ()):
        "policy_gate.validate_policy inlines the top-level set; "
        "no exported field-set constant exists.",
    ("bima-project.v1.schema.json", ()):
        "policy_gate.validate_project inlines the top-level set; "
        "no exported field-set constant exists.",
    ("bima-trusted-launcher-decision.v1.schema.json", ()):
        "trusted_policy_launcher._decision assembles the decision inline; "
        "no exported field-set constant exists.",
    ("bima-verification-aggregate.v1.schema.json", ()):
        "verification_aggregate.aggregate assembles the report inline; "
        "no exported field-set constant exists.",
    ("bima-verification-plan.v1.schema.json", ()):
        "verification_aggregate.validate_plan inlines the top-level set; "
        "no exported field-set constant exists.",
}


def schema_paths():
    return sorted(SCHEMA_DIR.glob("*" + SCHEMA_SUFFIX))


def load_schema(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name):
    path = ROOT / "automation" / (name + ".py")
    spec = importlib.util.spec_from_file_location("schema_parity_" + name, path)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load validator module: " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def node_at(document, path):
    node = document
    for key in path:
        node = node[key]
    return node


def mapped_keys():
    return {
        (filename, mapping[2])
        for filename, mappings in FIELD_SET_PARITY.items()
        for mapping in mappings
    }


class SchemaContractParityTests(unittest.TestCase):
    def test_schema_documents_are_valid_draft_2020_12_objects(self):
        paths = schema_paths()
        self.assertTrue(paths, "no schemas discovered")
        for path in paths:
            with self.subTest(schema=path.name):
                try:
                    document = load_schema(path)
                except (UnicodeError, json.JSONDecodeError) as exc:
                    self.fail(f"{path.name} is not valid UTF-8 JSON: {exc}")
                self.assertIsInstance(document, dict)

                self.assertEqual(document.get("$schema"), DRAFT_2020_12)
                title = document.get("title")
                self.assertIsInstance(title, str)
                self.assertTrue(title.strip())
                self.assertEqual(document.get("type"), "object")

                required = document.get("required")
                self.assertIsInstance(required, list)
                self.assertTrue(required)
                for field in required:
                    self.assertIsInstance(field, str)
                    self.assertTrue(field)
                self.assertEqual(len(required), len(set(required)))

                properties = document.get("properties")
                self.assertIsInstance(properties, dict)
                self.assertLessEqual(set(required), set(properties))
                self.assertIs(document.get("additionalProperties"), False)

    def test_schema_const_matches_filename(self):
        for path in schema_paths():
            with self.subTest(schema=path.name):
                document = load_schema(path)
                properties = document.get("properties")
                self.assertIsInstance(properties, dict)
                declaration = properties.get("schema")
                self.assertIsInstance(declaration, dict)
                value = declaration.get("const")
                self.assertIsInstance(value, str)
                self.assertTrue(value)
                self.assertEqual(value, path.name[:-len(SCHEMA_SUFFIX)])

    def test_schema_required_matches_validator_field_set(self):
        for filename, mappings in FIELD_SET_PARITY.items():
            for module_name, constant_name, node_path in mappings:
                label = module_name + "." + constant_name
                with self.subTest(schema=filename, field_set=label,
                                  path=node_path):
                    document = load_schema(SCHEMA_DIR / filename)
                    module = load_module(module_name)
                    self.assertTrue(
                        hasattr(module, constant_name),
                        f"{module_name} does not export {constant_name}",
                    )
                    field_set = getattr(module, constant_name)
                    self.assertIsInstance(field_set, (set, frozenset))

                    node = node_at(document, node_path)
                    self.assertIsInstance(node, dict)
                    required = node.get("required")
                    self.assertIsInstance(required, list)
                    self.assertEqual(set(required), set(field_set))

    def test_every_schema_top_level_is_mapped_or_explicitly_excepted(self):
        discovered = {path.name for path in schema_paths()}
        mapped = {
            filename for filename, mappings in FIELD_SET_PARITY.items()
            if any(mapping[2] == () for mapping in mappings)
        }
        excepted = {
            filename for filename, path in EXPLICIT_EXCEPTIONS if path == ()
        }

        self.assertEqual(mapped | excepted, discovered)
        self.assertFalse(mapped & excepted)
        self.assertLessEqual(set(FIELD_SET_PARITY), discovered)
        self.assertLessEqual(
            {filename for filename, _ in EXPLICIT_EXCEPTIONS}, discovered)

    def test_explicit_exceptions_are_documented(self):
        for (filename, node_path), reason in EXPLICIT_EXCEPTIONS.items():
            with self.subTest(schema=filename, path=node_path):
                self.assertNotIn((filename, node_path), mapped_keys())
                self.assertTrue(reason.strip())
                document = load_schema(SCHEMA_DIR / filename)
                node = node_at(document, node_path)
                self.assertIsInstance(node, dict)
                self.assertIsInstance(node.get("required"), list)


if __name__ == "__main__":
    unittest.main()
