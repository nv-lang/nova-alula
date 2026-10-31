"""Schema-aware canonical bytes for the integration value contract (model only)."""

from __future__ import annotations

import math
import hashlib
import json
import re
import struct
from collections.abc import Mapping
from typing import Any


PRIMITIVES = {"null", "bool", "i64", "f64", "str", "id"}
I64_MIN, I64_MAX = -(1 << 63), (1 << 63) - 1
SAFE_JSON_INTEGER = (1 << 53) - 1
TYPE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")


def _u64(n: int) -> bytes:
    if not 0 <= n < 1 << 64:
        raise ValueError("length outside u64")
    return struct.pack(">Q", n)


def _blob(b: bytes) -> bytes:
    return _u64(len(b)) + b


def _text(s: str) -> bytes:
    if not isinstance(s, str) or any(0xD800 <= ord(c) <= 0xDFFF for c in s):
        raise ValueError("text must contain Unicode scalar values")
    return _blob(s.encode("utf-8"))


def _type_signature(schema: Any) -> bytes:
    """Canonical descriptor bytes carried even by empty/absent containers."""
    if isinstance(schema, str) and schema not in PRIMITIVES:
        raise ValueError("unknown primitive")
    if not isinstance(schema, str) and not isinstance(schema, (Mapping, list)):
        raise ValueError("malformed schema descriptor")
    return _canonical_json_bytes(schema)


def _parse_i64_string(value: Any) -> int:
    if not isinstance(value, str) or re.fullmatch(r"(?:0|-[1-9][0-9]*|[1-9][0-9]*)", value) is None:
        raise ValueError("expected canonical decimal i64 string")
    parsed = int(value)
    if not I64_MIN <= parsed <= I64_MAX:
        raise ValueError("i64 string outside signed 64-bit range")
    return parsed


def _f64_text(x: float) -> bytes:
    if math.isnan(x):
        return b"NaN"
    if math.isinf(x):
        return b"-Infinity" if x < 0 else b"Infinity"
    if x == 0.0:
        return b"-0.0" if math.copysign(1.0, x) < 0 else b"0.0"
    # Python's binary64 repr is shortest-roundtrip; normalize only its notation.
    raw = repr(x).lower()
    m = re.fullmatch(r"(-?)(\d+)(?:\.(\d+))?(?:e([+-]?\d+))?", raw)
    assert m
    sign, whole, frac, exp = m.groups()
    frac = frac or ""
    exponent = int(exp or 0)
    digits = (whole + frac).lstrip("0") or "0"
    point = len(whole) + exponent
    leading = len((whole + frac)) - len((whole + frac).lstrip("0"))
    point -= leading
    digits = digits.rstrip("0") or "0"
    scientific_exp = point - 1
    if -6 <= scientific_exp < 21:
        if point <= 0:
            body = "0." + "0" * (-point) + digits
        elif point >= len(digits):
            body = digits + "0" * (point - len(digits)) + ".0"
        else:
            body = digits[:point] + "." + digits[point:]
    else:
        body = digits[0] + ("." + digits[1:] if len(digits) > 1 else ".0")
        body += "e" + ("+" if scientific_exp >= 0 else "-") + str(abs(scientific_exp))
    return (sign + body).encode("ascii")


def _check_name(name: Any, *, qualified: bool = False) -> None:
    if not isinstance(name, str) or not name or any(0xD800 <= ord(c) <= 0xDFFF for c in name):
        raise ValueError("name must be non-empty Unicode scalar text")
    if qualified and TYPE_NAME.fullmatch(name) is None:
        raise ValueError("declared type name must be qualified ASCII identifiers")


def _validate_declared_type(name: str, declarations: Mapping[str, Any], seen: set[str], aliases: set[str]) -> None:
    decl = declarations.get(name)
    if not isinstance(decl, Mapping) or not isinstance(decl.get("kind"), str):
        raise ValueError("missing or malformed declared type")
    kind = decl["kind"]
    if kind == "alias":
        if set(decl) != {"kind", "type"} or name in aliases:
            raise ValueError("malformed or recursive alias")
        aliases.add(name)
        _validate_schema(decl["type"], declarations, seen, aliases)
        aliases.remove(name)
        return
    if name in seen:
        return
    seen.add(name)
    if kind == "record":
        if set(decl) != {"kind", "fields"} or not isinstance(decl["fields"], Mapping):
            raise ValueError("record declaration must contain only fields")
        for field, field_schema in decl["fields"].items():
            _check_name(field)
            _validate_schema(field_schema, declarations, seen, set())
        return
    if kind == "variant":
        if set(decl) != {"kind", "cases"} or not isinstance(decl["cases"], Mapping) or not decl["cases"]:
            raise ValueError("variant declaration must contain non-empty cases")
        for case, fields in decl["cases"].items():
            _check_name(case)
            if not isinstance(fields, Mapping):
                raise ValueError("variant case must map fields")
            for field, field_schema in fields.items():
                _check_name(field)
                _validate_schema(field_schema, declarations, seen, set())
        return
    raise ValueError("declared type kind must be record, variant, or alias")


def _validate_schema(schema: Any, declarations: Mapping[str, Any], seen: set[str], aliases: set[str]) -> None:
    if isinstance(schema, str):
        if schema not in PRIMITIVES:
            raise ValueError("unknown primitive")
        return

    if not isinstance(schema, Mapping) or len(schema) != 1 or any(not isinstance(k, str) for k in schema):
        raise ValueError("malformed schema descriptor")
    kind, arg = next(iter(schema.items()))
    if kind == "list":
        _validate_schema(arg, declarations, seen, aliases)
    elif kind == "tuple":
        if not isinstance(arg, list) or len(arg) < 2: raise ValueError("tuple descriptor must have at least two ordered types")
        for item in arg: _validate_schema(item, declarations, seen, aliases)
    elif kind == "optional":
        _validate_schema(arg, declarations, seen, aliases)
    elif kind == "map":
        if not isinstance(arg, list) or len(arg) != 2: raise ValueError("map descriptor must have key and value type")
        _validate_schema(arg[0], declarations, seen, aliases)
        _validate_schema(arg[1], declarations, seen, aliases)
    elif kind == "int_min":
        _parse_i64_string(arg)
    elif kind == "literal_set":
        if not isinstance(arg, list) or len(arg) < 2 or any(not isinstance(v, str) for v in arg):
            raise ValueError("literal_set must contain at least two text values")
        for value in arg: _text(value)
        if arg != sorted(arg) or len(arg) != len(set(arg)): raise ValueError("literal_set values must be unique and sorted")
    elif kind == "full_map":
        if not isinstance(arg, list) or len(arg) != 2: raise ValueError("full_map descriptor must contain enum name and value type")
        _check_name(arg[0], qualified=True)
        enum_decl = declarations.get(arg[0])
        if not isinstance(enum_decl, Mapping) or enum_decl.get("kind") != "variant" or not isinstance(enum_decl.get("cases"), Mapping) or not enum_decl["cases"] or any(fields for fields in enum_decl["cases"].values()):
            raise ValueError("full_map key type must be a non-empty fieldless variant")
        _validate_declared_type(arg[0], declarations, seen, aliases)
        _validate_schema(arg[1], declarations, seen, aliases)
    elif kind in {"record", "variant", "named"}:
        _check_name(arg, qualified=True)
        expected = "alias" if kind == "named" else kind
        target = declarations.get(arg)
        if not isinstance(target, Mapping) or target.get("kind") != expected: raise ValueError("unknown or mismatched declared type")
        _validate_declared_type(arg, declarations, seen, aliases)
    else:
        raise ValueError("unknown schema constructor")


def validate_schema(schema: Any, declarations: Mapping[str, Any]) -> None:
    """Validate the full descriptor and declaration table before inspecting a value."""
    if not isinstance(declarations, Mapping):
        raise ValueError("declarations must be a mapping")
    seen: set[str] = set()
    for name, decl in declarations.items():
        _check_name(name, qualified=True)
        _validate_declared_type(name, declarations, seen, set())
    _validate_schema(schema, declarations, seen, set())


def _encode_typed(value: Any, schema: Any, declarations: Mapping[str, Any]) -> bytes:
    if isinstance(schema, str):
        if schema == "null":
            if value is not None: raise ValueError("expected null")
            return b"N"
        if schema == "bool":
            if type(value) is not bool: raise ValueError("expected bool")
            return b"B\x01" if value else b"B\x00"
        if schema == "i64":
            if type(value) is not int or not I64_MIN <= value <= I64_MAX: raise ValueError("expected i64")
            return b"I" + struct.pack(">q", value)
        if schema == "f64":
            if type(value) is not float: raise ValueError("expected f64")
            return b"F" + _blob(_f64_text(value))
        if schema == "str": return b"S" + _text(value)
        if schema == "id":
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value): raise ValueError("expected canonical id")
            return b"U" + bytes.fromhex(value.replace("-", ""))
    kind, arg = next(iter(schema.items()))
    if kind == "named":
        return b"Y" + _text(arg) + _blob(_encode_typed(value, declarations[arg]["type"], declarations))
    if kind == "list":
        if not isinstance(value, list): raise ValueError("expected list")
        return b"L" + _blob(_type_signature(arg)) + _u64(len(value)) + b"".join(_encode_typed(v, arg, declarations) for v in value)
    if kind == "tuple":
        if not isinstance(value, (list, tuple)) or len(value) != len(arg): raise ValueError("expected fixed tuple")
        return b"T" + _blob(_type_signature(arg)) + _u64(len(arg)) + b"".join(_encode_typed(v, s, declarations) for v, s in zip(value, arg))
    if kind == "optional":
        if not isinstance(value, Mapping): raise ValueError("optional uses none/some wrapper")
        header = b"O" + _blob(_type_signature(arg))
        if set(value) == {"none"} and type(value["none"]) is bool and value["none"] is True: return header + b"\x00"
        if set(value) == {"some"}: return header + b"\x01" + _encode_typed(value["some"], arg, declarations)
        raise ValueError("malformed optional wrapper")
    if kind == "map":
        if not isinstance(value, list): raise ValueError("map is a list of pairs")
        pairs = []
        for pair in value:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2: raise ValueError("map entry must be a key/value pair")
            pairs.append((_encode_typed(pair[0], arg[0], declarations), _encode_typed(pair[1], arg[1], declarations)))
        pairs.sort(key=lambda p: p[0])
        if any(pairs[i - 1][0] == pairs[i][0] for i in range(1, len(pairs))): raise ValueError("duplicate typed map key")
        return b"M" + _blob(_type_signature(arg[0])) + _blob(_type_signature(arg[1])) + _u64(len(pairs)) + b"".join(_blob(k) + _blob(v) for k, v in pairs)
    if kind == "int_min":
        bound = _parse_i64_string(arg)
        if type(value) is not int or not bound <= value <= I64_MAX: raise ValueError("value outside bounded i64")
        return b"J" + _blob(_type_signature(schema)) + struct.pack(">q", value)
    if kind == "literal_set":
        if not isinstance(value, str) or value not in arg: raise ValueError("value outside literal set")
        return b"C" + _blob(_type_signature(schema)) + _text(value)
    if kind == "full_map":
        if not isinstance(value, list): raise ValueError("full_map is a list of pairs")
        enum_name, value_schema = arg
        cases = declarations[enum_name]["cases"]
        expected = set(cases)
        pairs = []
        seen_cases = set()
        for pair in value:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2: raise ValueError("full_map entry must be a key/value pair")
            key = pair[0]
            if not isinstance(key, Mapping) or set(key) != {"case", "fields"} or not isinstance(key["case"], str) or key["fields"] != {}:
                raise ValueError("full_map key must be a fieldless enum case")
            case = key["case"]
            if case not in expected or case in seen_cases: raise ValueError("full_map must contain each enum case exactly once")
            seen_cases.add(case)
            pairs.append((_encode_typed(key, {"variant": enum_name}, declarations), _encode_typed(pair[1], value_schema, declarations)))
        if seen_cases != expected: raise ValueError("full_map must contain all enum cases")
        pairs.sort(key=lambda p: p[0])
        return b"G" + _blob(_type_signature(schema)) + _u64(len(pairs)) + b"".join(_blob(k) + _blob(v) for k, v in pairs)
    name = arg
    identity = _text(name)
    if kind == "record":
        fields = declarations[name]["fields"]
        if not isinstance(value, Mapping) or set(value) != set(fields): raise ValueError("record fields do not match schema")
        names = sorted(fields)
        return b"R" + identity + _u64(len(names)) + b"".join(_text(n) + _encode_typed(value[n], fields[n], declarations) for n in names)
    if not isinstance(value, Mapping) or set(value) != {"case", "fields"}: raise ValueError("variant uses case/fields")
    case = value["case"]
    fields = declarations[name]["cases"].get(case)
    if not isinstance(case, str) or not isinstance(fields, Mapping) or not isinstance(value["fields"], Mapping) or set(value["fields"]) != set(fields): raise ValueError("variant case/fields do not match schema")
    names = sorted(fields)
    return b"V" + identity + _text(case) + _u64(len(names)) + b"".join(_text(n) + _encode_typed(value["fields"][n], fields[n], declarations) for n in names)


def encode_typed(value: Any, schema: Any, declarations: Mapping[str, Any]) -> bytes:
    """Validate all schema declarations first, then encode the typed value."""
    validate_schema(schema, declarations)
    return _encode_typed(value, schema, declarations)


def _check_manifest(value: Any) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if not -(1 << 53) <= value <= SAFE_JSON_INTEGER: raise ValueError("manifest integer outside safe JSON integer range")
        return
    if type(value) is float:
        raise ValueError("manifest floats are forbidden")
    if isinstance(value, str):
        _text(value)
        return
    if isinstance(value, list):
        for item in value: _check_manifest(item)
        return
    if isinstance(value, Mapping):
        if any(not isinstance(k, str) for k in value): raise ValueError("manifest keys must be strings")
        for key, item in value.items(): _text(key); _check_manifest(item)
        return
    raise ValueError("unsupported manifest value")


MANIFEST_KEYS = {"alula_version", "machine", "revision", "types", "parties", "signals", "queries", "codec", "event_envelope"}
SUPPORTED_CODEC = {
    "domain": ["alias", "bool", "f64", "full_map", "i64", "id", "int_min", "list", "literal_set", "map", "null", "optional", "record", "str", "tuple", "variant"],
    "json": {"encoding": "UTF-8", "bom": False, "unicode_normalization": "none", "object_key_order": "Unicode code point", "arrays": "preserve", "string_escaping": "JSON-short-escapes; other-U+0000-001F-lowercase-u00xx; slash-literal", "duplicate_keys": "reject", "unknown_fields": "reject", "safe_integer_range": "-9007199254740992..9007199254740991"},
    "type_forms": {"alias": "declared-name-wraps-base", "bool": "json-boolean", "f64": "json-number-or-float-tag", "full_map": "array-of-all-enum-pairs", "i64": "canonical-decimal-json-string", "id": "lowercase-uuid-text", "int_min": "canonical-decimal-json-string-with-lower-bound", "list": "json-array-ordered", "literal_set": "json-string-in-closed-set", "map": "array-of-key-value-pairs", "null": "json-null", "optional": "none-some-object", "record": "json-object-with-exact-fields", "str": "json-string", "tuple": "json-array-fixed-arity-at-least-two", "variant": "case-fields-object"},
    "typed_bytes": {"length": "u64-big-endian", "text": "length-prefixed-UTF-8", "f64": "length-prefixed-ASCII", "markers": {"alias": "Y", "bool": "B", "f64": "F", "full_map": "G", "i64": "I", "id": "U", "int_min": "J", "list": "L", "literal_set": "C", "map": "M", "null": "N", "optional": "O", "record": "R", "str": "S", "tuple": "T", "variant": "V"}},
    "i64": {"wire": "canonical-decimal-json-string", "minimum": "-9223372036854775808", "maximum": "9223372036854775807"},
    "int_min": {"form": "int>=n", "bound": "inclusive-lower-bound"},
    "literal_set": {"minimum_values": 2, "unique": True, "order": "Unicode code point"},
    "full_map": {"key_type": "fieldless-enum", "coverage": "all-cases-exactly-once"},
    "f64": {"finite": "shortest-roundtrip-decimal", "tie_break": "nearest-then-even", "fixed_exponent_min": -6, "fixed_exponent_max": 20, "nan": "NaN", "positive_infinity": "Infinity", "negative_infinity": "-Infinity", "negative_zero": "-0.0", "positive_zero": "0.0", "json_finite": "number-same-binary64", "json_specials": "$float-tag", "nan_payload": "discard"},
    "digest": {"algorithm": "SHA-256", "domain": "alula-value-digest", "separator_hex": "00", "representation": "sha256:lowercase-hex-64"},
}
SUPPORTED_EVENT_ENVELOPE = {
    "required_fields": ["contract_id", "data", "event_id", "event_kind", "instance_id"],
    "unknown_fields": "reject", "event_id": "logical-event-not-rpc-call", "instance_id": "non-reusable",
    "contract_binding": "contract_id-equals-instance-contract-pin", "data": "object-selected-by-event-kind-schema",
    "event_kinds": [
        {"name": "machine.control", "required_fields": ["signal"], "conditional_fields": {"pause_id": "parent-continue-only", "request_id": "parent-owned-control-only"}, "data_shape": "control-data"},
        {"name": "party.signal", "required_fields": ["party", "signal"], "conditional_fields": {"gate_id": "gate-signal-only", "subject_id": "subject-bound-gate-only"}, "data_shape": "declared-signal-fields"},
        {"name": "request.failure", "required_fields": ["party", "request_id"], "conditional_fields": {}, "data_shape": "code-and-message"},
        {"name": "request.reply", "required_fields": ["party", "request_id"], "conditional_fields": {}, "data_shape": "result-only"},
    ],
}


def _named_fields(value: Any, declarations: Mapping[str, Any] | None = None) -> None:
    if not isinstance(value, list): raise ValueError("fields must be an array")
    names = []
    for field in value:
        if not isinstance(field, Mapping) or set(field) != {"name", "type"}: raise ValueError("field declaration shape is invalid")
        _check_name(field["name"])
        names.append(field["name"])
    if names != sorted(names) or len(names) != len(set(names)):
        raise ValueError("field declarations must be uniquely sorted by name")


def _manifest_projection(manifest: Any) -> None:
    if not isinstance(manifest, Mapping) or set(manifest) != MANIFEST_KEYS:
        raise ValueError("manifest must have exactly the public projection keys")
    for key in ("alula_version", "machine"):
        _check_name(manifest[key])
    if type(manifest["revision"]) is not int or not 0 <= manifest["revision"] <= SAFE_JSON_INTEGER:
        raise ValueError("revision must be a non-negative safe JSON integer")
    types = manifest["types"]
    if not isinstance(types, Mapping) or set(types) != {"aliases", "records", "variants"}:
        raise ValueError("types projection must contain aliases, records, and variants")
    declared: dict[str, Any] = {}
    for kind in ("aliases", "records", "variants"):
        declarations = types[kind]
        if not isinstance(declarations, list): raise ValueError("type declarations must be arrays")
        names = []
        for item in declarations:
            if not isinstance(item, Mapping): raise ValueError("type declaration must be an object")
            name = item.get("name")
            _check_name(name, qualified=True)
            names.append(name)
            if kind == "aliases":
                if set(item) != {"name", "type"}: raise ValueError("alias manifest declaration has unknown/missing keys")
                declared[name] = {"kind": "alias", "type": item["type"]}
            elif kind == "records":
                if set(item) != {"name", "fields"}: raise ValueError("record manifest declaration has unknown/missing keys")
                _named_fields(item["fields"], declared)
                fields = {f["name"]: f["type"] for f in item["fields"]}
                declared[name] = {"kind": "record", "fields": fields}
            else:
                if set(item) != {"name", "cases"} or not isinstance(item["cases"], list): raise ValueError("variant manifest declaration has unknown/missing keys")
                case_names = []
                cases = {}
                for case in item["cases"]:
                    if not isinstance(case, Mapping) or set(case) != {"name", "fields"}: raise ValueError("variant case declaration has invalid shape")
                    _check_name(case["name"])
                    case_names.append(case["name"])
                    _named_fields(case["fields"], declared)
                    cases[case["name"]] = {f["name"]: f["type"] for f in case["fields"]}
                if not case_names or case_names != sorted(case_names) or len(case_names) != len(set(case_names)):
                    raise ValueError("variant cases must be non-empty, unique and sorted")
                declared[name] = {"kind": "variant", "cases": cases}
        if names != sorted(names) or len(names) != len(set(names)):
            raise ValueError("declared types must be uniquely sorted by name")
    if len(declared) != sum(len(types[k]) for k in ("aliases", "records", "variants")):
        raise ValueError("declared type names must be globally unique")
    validate_schema("null", declared)
    parties = manifest["parties"]
    if not isinstance(parties, list): raise ValueError("parties must be an array")
    party_names = []
    for party in parties:
        if not isinstance(party, Mapping) or set(party) != {"name", "kind", "inputs", "result"}:
            raise ValueError("party declaration has unknown/missing keys")
        _check_name(party["name"]); _check_name(party["kind"])
        _named_fields(party["inputs"], declared)
        for field in party["inputs"]: _validate_schema(field["type"], declared, set(), set())
        if party["result"] is not None: _validate_schema(party["result"], declared, set(), set())
        party_names.append(party["name"])
    if party_names != sorted(party_names) or len(party_names) != len(set(party_names)):
        raise ValueError("parties must be uniquely sorted by name")
    signals = manifest["signals"]
    if not isinstance(signals, list): raise ValueError("signals must be an array")
    party_name_set = set(party_names)
    signal_keys = []
    for signal in signals:
        if not isinstance(signal, Mapping) or set(signal) != {"name", "party", "fields"}:
            raise ValueError("signal declaration has unknown/missing keys")
        _check_name(signal["name"])
        if signal["party"] is not None: _check_name(signal["party"])
        if signal["party"] is not None and signal["party"] not in party_name_set:
            raise ValueError("signal references undeclared party")
        _named_fields(signal["fields"], declared)
        for field in signal["fields"]: _validate_schema(field["type"], declared, set(), set())
        signal_keys.append((signal["party"] or "", signal["name"]))
    if signal_keys != sorted(signal_keys) or len(signal_keys) != len(set(signal_keys)):
        raise ValueError("signals must be uniquely sorted by party and name")
    queries = manifest["queries"]
    if not isinstance(queries, list): raise ValueError("queries must be an array")
    query_names = []
    for query in queries:
        if not isinstance(query, Mapping) or set(query) != {"name", "inputs", "result"}:
            raise ValueError("query declaration has unknown/missing keys")
        _check_name(query["name"]); _named_fields(query["inputs"], declared)
        for field in query["inputs"]: _validate_schema(field["type"], declared, set(), set())
        _validate_schema(query["result"], declared, set(), set())
        query_names.append(query["name"])
    if query_names != sorted(query_names) or len(query_names) != len(set(query_names)):
        raise ValueError("queries must be uniquely sorted by name")
    codec = manifest["codec"]
    codec_keys = {"domain", "json", "type_forms", "typed_bytes", "i64", "int_min", "literal_set", "full_map", "f64", "digest"}
    if not isinstance(codec, Mapping) or set(codec) != codec_keys:
        raise ValueError("codec projection has unknown/missing semantic material")
    expected_domain = ["alias", "bool", "f64", "full_map", "i64", "id", "int_min", "list", "literal_set", "map", "null", "optional", "record", "str", "tuple", "variant"]
    if not isinstance(codec["domain"], list) or codec["domain"] != expected_domain or any(not isinstance(x, str) for x in codec["domain"]):
        raise ValueError("codec domain must be a sorted unique string array")
    json_codec = codec["json"]
    if not isinstance(json_codec, Mapping) or set(json_codec) != {"encoding", "bom", "unicode_normalization", "object_key_order", "arrays", "string_escaping", "duplicate_keys", "unknown_fields", "safe_integer_range"}:
        raise ValueError("manifest JSON codec descriptor has unknown/missing keys")
    if type(json_codec["bom"]) is not bool or any(not isinstance(json_codec[k], str) for k in set(json_codec) - {"bom"}):
        raise ValueError("JSON codec descriptor has invalid field types")
    type_forms = codec["type_forms"]
    expected_forms = {"alias", "bool", "f64", "full_map", "i64", "id", "int_min", "list", "literal_set", "map", "null", "optional", "record", "str", "tuple", "variant"}
    if not isinstance(type_forms, Mapping) or set(type_forms) != expected_forms or any(not isinstance(v, str) for v in type_forms.values()):
        raise ValueError("JSON type-form table must be complete and explicit")
    bytes_codec = codec["typed_bytes"]
    if not isinstance(bytes_codec, Mapping) or set(bytes_codec) != {"length", "text", "f64", "markers"}:
        raise ValueError("typed-bytes codec descriptor has unknown/missing keys")
    if not all(isinstance(bytes_codec[k], str) for k in ("length", "text", "f64")):
        raise ValueError("typed-bytes codec descriptor fields must be strings")
    markers = bytes_codec["markers"]
    if not isinstance(markers, Mapping) or set(markers) != set(codec["domain"]):
        raise ValueError("typed-bytes marker set must describe the whole codec domain")
    if any(not isinstance(marker, str) or len(marker) != 1 for marker in markers.values()) or len(set(markers.values())) != len(markers):
        raise ValueError("typed-bytes markers must be distinct one-character strings")
    for key in ("i64", "int_min", "literal_set", "full_map", "f64", "digest"):
        if not isinstance(codec[key], Mapping) or not codec[key]: raise ValueError(f"codec.{key} must be a non-empty semantic object")
    if set(codec["i64"]) != {"wire", "minimum", "maximum"} or any(not isinstance(v, str) for v in codec["i64"].values()):
        raise ValueError("i64 wire/range descriptor is incomplete")
    if set(codec["int_min"]) != {"form", "bound"} or any(not isinstance(v, str) for v in codec["int_min"].values()):
        raise ValueError("bounded integer descriptor is incomplete")
    if set(codec["literal_set"]) != {"minimum_values", "unique", "order"} or type(codec["literal_set"]["minimum_values"]) is not int or type(codec["literal_set"]["unique"]) is not bool or not isinstance(codec["literal_set"]["order"], str):
        raise ValueError("literal-set descriptor is incomplete or mistyped")
    if set(codec["full_map"]) != {"key_type", "coverage"} or any(not isinstance(v, str) for v in codec["full_map"].values()):
        raise ValueError("full-map descriptor is incomplete")
    if set(codec["f64"]) != {"finite", "tie_break", "fixed_exponent_min", "fixed_exponent_max", "nan", "positive_infinity", "negative_infinity", "negative_zero", "positive_zero", "json_finite", "json_specials", "nan_payload"}:
        raise ValueError("f64 descriptor has unknown/missing semantic fields")
    if type(codec["f64"]["fixed_exponent_min"]) is not int or type(codec["f64"]["fixed_exponent_max"]) is not int or any(not isinstance(codec["f64"][k], str) for k in set(codec["f64"]) - {"fixed_exponent_min", "fixed_exponent_max"}):
        raise ValueError("f64 descriptor has invalid field types")
    if set(codec["digest"]) != {"algorithm", "domain", "separator_hex", "representation"} or any(not isinstance(v, str) for v in codec["digest"].values()):
        raise ValueError("typed digest descriptor is incomplete")
    envelope = manifest["event_envelope"]
    if not isinstance(envelope, Mapping) or set(envelope) != {"required_fields", "unknown_fields", "event_id", "instance_id", "contract_binding", "data", "event_kinds"}:
        raise ValueError("event envelope projection has unknown/missing semantic fields")
    expected_required = ["contract_id", "data", "event_id", "event_kind", "instance_id"]
    if envelope["required_fields"] != expected_required or envelope["unknown_fields"] != "reject":
        raise ValueError("event envelope required/unknown-field rules do not match the protocol")
    if any(not isinstance(envelope[k], str) for k in ("event_id", "instance_id", "contract_binding", "data")):
        raise ValueError("event envelope semantic values must be strings")
    event_kinds = envelope["event_kinds"]
    if not isinstance(event_kinds, list): raise ValueError("event_kinds must be an array")
    event_names = []
    for event in event_kinds:
        if not isinstance(event, Mapping) or set(event) != {"name", "required_fields", "conditional_fields", "data_shape"}:
            raise ValueError("event kind semantic descriptor has invalid shape")
        _check_name(event["name"])
        if not isinstance(event["required_fields"], list) or any(not isinstance(x, str) for x in event["required_fields"]) or event["required_fields"] != sorted(set(event["required_fields"])):
            raise ValueError("event kind required fields must be sorted unique strings")
        if not isinstance(event["conditional_fields"], Mapping) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in event["conditional_fields"].items()):
            raise ValueError("event kind conditional fields must map names to semantic conditions")
        if not isinstance(event["data_shape"], str): raise ValueError("event kind data shape must be a string")
        event_names.append(event["name"])
    if event_names != sorted(event_names) or len(event_names) != len(set(event_names)):
        raise ValueError("event kinds must be uniquely sorted by name")
    expected_events = ["machine.control", "party.signal", "request.failure", "request.reply"]
    if event_names != expected_events:
        raise ValueError("manifest must cover all event envelope kinds")
    events_by_name = {event["name"]: event for event in event_kinds}
    expected_required = {
        "machine.control": ["signal"],
        "party.signal": ["party", "signal"],
        "request.failure": ["party", "request_id"],
        "request.reply": ["party", "request_id"],
    }
    expected_conditional = {
        "machine.control": {"pause_id", "request_id"},
        "party.signal": {"gate_id", "subject_id"},
        "request.failure": set(),
        "request.reply": set(),
    }
    if any(events_by_name[name]["required_fields"] != fields or set(events_by_name[name]["conditional_fields"]) != expected_conditional[name] for name, fields in expected_required.items()):
        raise ValueError("event kind field dependency is incomplete")
    if codec != SUPPORTED_CODEC:
        raise ValueError("manifest codec semantic values are not the supported canonical profile")
    if envelope != SUPPORTED_EVENT_ENVELOPE:
        raise ValueError("manifest event-envelope semantic values are not the supported protocol profile")
    _check_manifest(manifest)


def _canonical_json_bytes(value: Any) -> bytes:
    _check_manifest(value)
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return text.encode("utf-8")


def canonical_manifest_bytes(manifest: Any) -> bytes:
    """Canonical bytes of the exact public contract projection, never arbitrary JSON."""
    _manifest_projection(manifest)
    return _canonical_json_bytes(manifest)


def parse_manifest_json(source: str | bytes) -> Any:
    """Strictly parse the manifest projection, rejecting duplicate keys and floats."""
    if isinstance(source, bytes):
        source = source.decode("utf-8", errors="strict")
    if not isinstance(source, str): raise ValueError("manifest JSON must be UTF-8 text")
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in items:
            if key in result: raise ValueError("duplicate JSON object key")
            result[key] = value
        return result
    def reject_number(token: str) -> Any:
        raise ValueError("manifest JSON numbers must be integers")
    value = json.loads(source, object_pairs_hook=pairs, parse_float=reject_number, parse_constant=reject_number)
    canonical_manifest_bytes(value)
    return value


def value_digest(value: Any, schema: Any, declarations: Mapping[str, Any]) -> str:
    material = b"alula-value-digest\x00" + encode_typed(value, schema, declarations)
    return "sha256:" + hashlib.sha256(material).hexdigest()


def contract_id(manifest: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_manifest_bytes(manifest)).hexdigest()
