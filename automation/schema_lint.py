"""Structural lint for schemas/*.schema.json; not a JSON Schema validator."""

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = "schemas/*.schema.json"
NODE_MAPS = ("properties", "patternProperties", "$defs", "definitions", "dependentSchemas")
NODE_VALUES = ("items", "not", "contains", "propertyNames", "if", "then", "else",
               "additionalProperties")
NODE_LISTS = ("allOf", "anyOf", "oneOf", "prefixItems")


class LintError(RuntimeError):
    """A schema breaks a repository structural rule."""


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"non-finite number: {value}")


def load_json(path, label):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise LintError(f"{label}: cannot read: {exc}") from exc
    try:
        return json.loads(text, object_pairs_hook=reject_duplicates,
                          parse_constant=reject_constant)
    except ValueError as exc:
        raise LintError(f"{label}: invalid JSON: {exc}") from exc


def escape(token):
    return token.replace("~", "~0").replace("/", "~1")


def json_type(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    return "array" if isinstance(value, list) else "object"


def resolve(document, pointer, where):
    node = document
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and token in node:
            node = node[token]
        elif isinstance(node, list) and token.isdigit() and int(token) < len(node):
            node = node[int(token)]
        else:
            raise LintError(f"{where}: unresolved local $ref: #{pointer}")
    return node


def check_required(node, where):
    if "required" not in node:
        return
    required = node["required"]
    if not isinstance(required, list) or not all(isinstance(name, str) for name in required):
        raise LintError(f"{where}: required must be a list of strings")
    if len(set(required)) != len(required):
        raise LintError(f"{where}: duplicate required name")
    properties = node.get("properties")
    if isinstance(properties, dict):
        for name in required:
            if name not in properties:
                raise LintError(f"{where}: required name is not in properties: {name}")


def declares_object(node):
    declared = node.get("type")
    declared = [declared] if isinstance(declared, str) else declared
    # if/then/oneOf fragments constrain named properties without declaring a shape.
    return isinstance(declared, list) and "object" in declared


def check_open_object(node, where):
    if not isinstance(node.get("properties"), dict) or not declares_object(node):
        return
    if "additionalProperties" not in node:
        raise LintError(f"{where}: missing additionalProperties")
    extra = node["additionalProperties"]
    if extra is True or not isinstance(extra, (bool, dict)):
        raise LintError(f"{where}: additionalProperties must be false or a schema object")


def check_pattern(node, where):
    if "pattern" not in node:
        return
    pattern = node["pattern"]
    if not isinstance(pattern, str):
        raise LintError(f"{where}: pattern must be a string")
    try:
        re.compile(pattern)
    except re.error as exc:
        raise LintError(f"{where}: invalid pattern: {exc}") from exc


def check_const(node, where):
    if "const" not in node or "type" not in node:
        return
    declared = node["type"]
    declared = [declared] if isinstance(declared, str) else declared
    if not isinstance(declared, list) or not all(isinstance(name, str) for name in declared):
        return
    actual = json_type(node["const"])
    if actual not in declared and not (actual == "integer" and "number" in declared):
        raise LintError(f"{where}: const type {actual} contradicts type {declared}")


def check_node(document, node, where, refs, defs):
    reference = node.get("$ref")
    if isinstance(reference, str):
        refs.add(reference)
        if reference.startswith("#"):
            pointer = reference[1:]
            if pointer and not pointer.startswith("/"):
                raise LintError(f"{where}: unsupported local $ref: {reference}")
            resolve(document, pointer, where)
    definitions = node.get("$defs")
    if isinstance(definitions, dict):
        for name in definitions:
            defs.append((f"{where}/$defs/{escape(name)}", name))
    check_required(node, where)
    check_open_object(node, where)
    check_pattern(node, where)
    check_const(node, where)


def walk(document, node, where, refs, defs):
    if not isinstance(node, dict):
        return
    check_node(document, node, where, refs, defs)
    for key in NODE_MAPS:
        children = node.get(key)
        if isinstance(children, dict):
            for name, child in children.items():
                walk(document, child, f"{where}/{escape(key)}/{escape(name)}", refs, defs)
    for key in NODE_VALUES:
        child = node.get(key)
        if isinstance(child, dict):
            walk(document, child, f"{where}/{escape(key)}", refs, defs)
    for key in NODE_LISTS:
        children = node.get(key)
        if isinstance(children, list):
            for index, child in enumerate(children):
                walk(document, child, f"{where}/{escape(key)}/{index}", refs, defs)


def check(document):
    if not isinstance(document, dict):
        raise LintError("schema must be a JSON object")
    refs, defs = set(), []
    walk(document, document, "#", refs, defs)
    for pointer, name in defs:
        if pointer not in refs:
            raise LintError(f"$defs entry is never referenced: {name}")


def validate(root):
    root = root.resolve()
    paths = sorted(path for path in root.glob(SCHEMAS) if path.is_file())
    if not paths:
        raise LintError(f"no {SCHEMAS} files found")
    for path in paths:
        label = path.relative_to(root).as_posix()
        document = load_json(path, label)
        try:
            check(document)
        except LintError as exc:
            raise LintError(f"{label}: {exc}") from exc
    return len(paths)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Structurally lint schemas/*.schema.json without validating instances.")
    parser.add_argument("--root", type=Path, default=ROOT)
    arguments = parser.parse_args(argv)
    try:
        count = validate(arguments.root)
    except (LintError, OSError) as exc:
        print(f"schema-lint: fail: {exc}", file=sys.stderr)
        return 2
    print(f"schema-lint: pass; schemas={count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
