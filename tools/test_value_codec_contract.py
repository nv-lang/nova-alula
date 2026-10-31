"""Executable probes for the candidate typed-byte contract; not runtime conformance."""

from __future__ import annotations

import copy
import json
import math
import struct
import sys
import unittest

from event_protocol_model import _freeze
from typed_value_codec import _canonical_json_bytes, canonical_manifest_bytes, contract_id, encode_typed, parse_manifest_json, value_digest


CODEC_PROJECTION = {
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
ENVELOPE_PROJECTION = {
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


class ValueCodecContractTests(unittest.TestCase):
    def test_existing_semantics_signed_zero_nan_and_infinities(self):
        self.assertNotEqual(_freeze(-0.0), _freeze(0.0))
        nan_a = struct.unpack(">d", bytes.fromhex("7ff8000000000001"))[0]
        nan_b = struct.unpack(">d", bytes.fromhex("7ff8000000000002"))[0]
        self.assertNotEqual(struct.pack(">d", nan_a), struct.pack(">d", nan_b))
        self.assertEqual(_freeze(nan_a), _freeze(nan_b))
        self.assertNotEqual(_freeze(math.inf), _freeze(-math.inf))

    def test_equivalent_f64_json_spellings_after_typed_parse(self):
        decoded = [float(json.loads(token)) for token in ("1", "1.0", "1e0")]
        self.assertEqual(len({_freeze(v) for v in decoded}), 1)

    def test_finite_binary64_json_roundtrip_at_edges_and_neighbors(self):
        values = (5e-324, math.nextafter(5e-324, math.inf), math.nextafter(1.0, 0.0), 1.0,
                  math.nextafter(1.0, math.inf), math.nextafter(sys.float_info.max, 0.0),
                  sys.float_info.max, -0.0)
        for value in values:
            with self.subTest(value=value):
                decoded = json.loads(json.dumps(value, allow_nan=False))
                self.assertEqual(struct.pack(">d", value), struct.pack(">d", decoded))

    def test_fixed_typed_byte_and_digest_vectors(self):
        vectors = (
            (None, "null", {}, "4e", "sha256:ea86c4d25a8869b9d585b0b8ea94c8bde13675774d82d9ede17af430b10d42aa"),
            (True, "bool", {}, "4201", "sha256:9efe53517fd0b46dfb21dbd5f6552dfb6f02174c453789aa545a45b37a318803"),
            (1, "i64", {}, "490000000000000001", "sha256:f126d51495c11d6233a6a018928a1ad62a344de07eaaf9775ffd3888135fae4e"),
            ("1", "str", {}, "53000000000000000131", "sha256:8546005a741bdb09df588b4daa0ebf0abe3f81d1fd53fae393c5f254d52f72d8"),
            ([1], {"list": "i64"}, {}, "4c000000000000000522693634220000000000000001490000000000000001", "sha256:6de946c6f9fc52edb75bc7df8d2fdffd2d86396b6d0e230b313aa2466eb157bc"),
            ([1, "a"], {"tuple": ["i64", "str"]}, {}, "54000000000000000d5b22693634222c22737472225d000000000000000249000000000000000153000000000000000161", "sha256:c728f34ab735bff907988def54b8fa023f8cca810972ad7f555b899d23e5fc80"),
            ({"none": True}, {"optional": "i64"}, {}, "4f0000000000000005226936342200", "sha256:43326dc8abcac04352fec30ffd178ada5827e428c26186ce3a748b4ceb9c13f1"),
            (-0.0, "f64", {}, "4600000000000000042d302e30", "sha256:e2fcecc4e56d14a2049e1797484760e3364868f950c5bb1ac17d7831cf648704"),
            (0.0, "f64", {}, "460000000000000003302e30", "sha256:2b80404fb011ead8ae5cb9545a2a89a1b1f1f48455b1529c7700d9b9249ee516"),
        )
        for value, schema, decls, expected_bytes, expected_digest in vectors:
            with self.subTest(schema=schema, value=value):
                self.assertEqual(encode_typed(value, schema, decls).hex(), expected_bytes)
                self.assertEqual(value_digest(value, schema, decls), expected_digest)
        some = {"some": 1}
        optional = {"optional": "i64"}
        self.assertEqual(encode_typed(some, optional, {}).hex(), "4f0000000000000005226936342201490000000000000001")
        self.assertEqual(value_digest(some, optional, {}), "sha256:eb12a5ad84315deba619ff967a352897e68fc09947f9d0b618d85c961d513d63")

    def test_fixed_map_and_variant_vectors(self):
        map_schema = {"map": ["str", "i64"]}
        map_value = [["a", 1]]
        map_bytes = "4d00000000000000052273747222000000000000000522693634220000000000000001000000000000000a530000000000000001610000000000000009490000000000000001"
        self.assertEqual(encode_typed(map_value, map_schema, {}).hex(), map_bytes)
        self.assertEqual(value_digest(map_value, map_schema, {}), "sha256:94c94f53b028c8150506f07afe04ed57faac5184062ec865b55bc07749e3caee")
        declarations = {"pkg.V1": {"kind": "variant", "cases": {"Some": {"x": {"optional": "i64"}}}}}
        variant = {"case": "Some", "fields": {"x": {"none": True}}}
        variant_bytes = "560000000000000006706b672e56310000000000000004536f6d6500000000000000010000000000000001784f0000000000000005226936342200"
        self.assertEqual(encode_typed(variant, {"variant": "pkg.V1"}, declarations).hex(), variant_bytes)
        self.assertEqual(value_digest(variant, {"variant": "pkg.V1"}, declarations), "sha256:0d08faee15cc92ab8267c0e48e5626adb0d32d3e1249393244bcf6d954c5d0f7")

    def test_fixed_numeric_bound_literal_set_and_full_map_vectors(self):
        bounded = {"int_min": "1"}
        expected_bounded = "4a000000000000000f7b22696e745f6d696e223a2231227d0000000000000001"
        self.assertEqual(encode_typed(1, bounded, {}).hex(), expected_bounded)
        self.assertEqual(value_digest(1, bounded, {}), "sha256:c2fefc80109beb5c07151a390e0d325484b8947615fe5265b42b4ab89a360d3c")
        literals = {"literal_set": ["a", "b"]}
        expected_literal = "4300000000000000197b226c69746572616c5f736574223a5b2261222c2262225d7d000000000000000161"
        self.assertEqual(encode_typed("a", literals, {}).hex(), expected_literal)
        self.assertEqual(value_digest("a", literals, {}), "sha256:722ddc641d5492aa837b80fc1c785dc05039b4d77fbb4247feb8f49f203d6de5")
        declarations = {"pkg.Mode": {"kind": "variant", "cases": {"A": {}, "B": {}}}}
        schema = {"full_map": ["pkg.Mode", "str"]}
        value = [[{"case": "A", "fields": {}}, "a"], [{"case": "B", "fields": {}}, "b"]]
        expected_full = "47000000000000001f7b2266756c6c5f6d6170223a5b22706b672e4d6f6465222c22737472225d7d00000000000000020000000000000022560000000000000008706b672e4d6f64650000000000000001410000000000000000000000000000000a530000000000000001610000000000000022560000000000000008706b672e4d6f64650000000000000001420000000000000000000000000000000a53000000000000000162"
        self.assertEqual(encode_typed(value, schema, declarations).hex(), expected_full)
        self.assertEqual(value_digest(value, schema, declarations), "sha256:5fcc7efd21a9b158818eaf8aa50e8cf6c46c298eb20ed28d113a7c7cba68a823")
        for bad_value, bad_schema in ((0, bounded), ("c", literals)):
            with self.subTest(value=bad_value), self.assertRaises(ValueError): encode_typed(bad_value, bad_schema, {})
        with self.assertRaises(ValueError): encode_typed(value[:1], schema, declarations)

    def test_new_encoder_collapses_nan_payload_and_fixes_special_float_vectors(self):
        nan_a = struct.unpack(">d", bytes.fromhex("7ff8000000000001"))[0]
        nan_b = struct.unpack(">d", bytes.fromhex("7ff8000000000002"))[0]
        expected_nan = "4600000000000000034e614e"
        expected_nan_digest = "sha256:fe4460b654e3b3d2c376686bc5de8263df70332f22a23237bb4a468a0c2e4ae8"
        self.assertEqual(encode_typed(nan_a, "f64", {}).hex(), expected_nan)
        self.assertEqual(encode_typed(nan_b, "f64", {}).hex(), expected_nan)
        self.assertEqual(value_digest(nan_a, "f64", {}), expected_nan_digest)
        for value, expected, digest in (
            (math.inf, "460000000000000008496e66696e697479", "sha256:d611988263ab0d000d5648b694c66436b82edd3e6e31d8fae810a408a6142be5"),
            (-math.inf, "4600000000000000092d496e66696e697479", "sha256:f3f40eaf25087768bf640b3970c98daad123b3db2ea24c509df6876d835fd19b"),
        ):
            self.assertEqual(encode_typed(value, "f64", {}).hex(), expected)
            self.assertEqual(value_digest(value, "f64", {}), digest)

    def test_nominal_records_with_identical_shape_are_distinct(self):
        declarations = {"pkg.A": {"kind": "record", "fields": {"x": "i64"}},
                        "pkg.B": {"kind": "record", "fields": {"x": "i64"}}}
        a = encode_typed({"x": 1}, {"record": "pkg.A"}, declarations)
        b = encode_typed({"x": 1}, {"record": "pkg.B"}, declarations)
        self.assertNotEqual(a, b)
        self.assertEqual(a.hex(), "520000000000000005706b672e410000000000000001000000000000000178490000000000000001")
        self.assertEqual(value_digest({"x": 1}, {"record": "pkg.A"}, declarations),
                         "sha256:c18a00bd335b1c2e769edd475e6a6b2f1715b4833156619fcf15f65c89aa1fd0")
        self.assertEqual(value_digest({"x": 1}, {"record": "pkg.B"}, declarations),
                         "sha256:f2f0376516c294c44bfa493b13cc45d8baeb5997a9e58da182b173a16fda17e1")

    def test_variant_identity_and_optional_field_marker_are_schema_aware(self):
        declarations = {
            "pkg.V1": {"kind": "variant", "cases": {"Some": {"x": {"optional": "i64"}}}},
            "pkg.V2": {"kind": "variant", "cases": {"Some": {"x": {"optional": "i64"}}}},
        }
        value = {"case": "Some", "fields": {"x": {"none": True}}}
        first = encode_typed(value, {"variant": "pkg.V1"}, declarations)
        second = encode_typed(value, {"variant": "pkg.V2"}, declarations)
        self.assertNotEqual(first, second)
        self.assertTrue(first.endswith(bytes.fromhex("4f0000000000000005226936342200")))
        self.assertNotEqual(encode_typed({"none": True}, {"optional": "i64"}, {}), first)
        self.assertNotEqual(encode_typed([], {"list": "i64"}, {}), encode_typed([], {"list": "str"}, {}))
        self.assertNotEqual(encode_typed({"none": True}, {"optional": "i64"}, {}), encode_typed({"none": True}, {"optional": "str"}, {}))

    def test_string_bytes_are_utf8_without_normalization(self):
        composed = encode_typed("é", "str", {})
        decomposed = encode_typed("e\u0301", "str", {})
        self.assertEqual(composed.hex(), "530000000000000002c3a9")
        self.assertEqual(decomposed.hex(), "53000000000000000365cc81")
        self.assertNotEqual(composed, decomposed)

    def test_canonical_manifest_unicode_order_escapes_and_array_order(self):
        manifest = {"é": "line\n\t/\"\\", "z": "é", "items": [2, 1]}
        self.assertEqual(_canonical_json_bytes(manifest),
                         '{"items":[2,1],"z":"é","é":"line\\n\\t/\\\"\\\\"}'.encode("utf-8"))
        self.assertNotEqual(_canonical_json_bytes({"items": [2, 1]}),
                            _canonical_json_bytes({"items": [1, 2]}))

    def test_map_order_and_duplicate_typed_keys(self):
        schema = {"map": ["str", "i64"]}
        self.assertEqual(encode_typed([["b", 2], ["a", 1]], schema, {}),
                         encode_typed([["a", 1], ["b", 2]], schema, {}))
        with self.assertRaises(ValueError):
            encode_typed([["a", 1], ["a", 2]], schema, {})

    def test_f64_canonical_decimal_tie_exponent_and_specials(self):
        self.assertEqual(encode_typed(1.0, "f64", {}).hex(), "460000000000000003312e30")
        self.assertEqual(encode_typed(1e-6, "f64", {}).hex(), "460000000000000008302e303030303031")
        self.assertEqual(encode_typed(1e-7, "f64", {}).hex(), "460000000000000006312e30652d37")
        self.assertEqual(encode_typed(math.inf, "f64", {}).hex(), "460000000000000008496e66696e697479")
        self.assertEqual(encode_typed(-math.inf, "f64", {}).hex(), "4600000000000000092d496e66696e697479")
        self.assertEqual(encode_typed(float("nan"), "f64", {}).hex(), "4600000000000000034e614e")
        for value, token in ((5e-324, b"5.0e-324"), (math.nextafter(5e-324, math.inf), b"1.0e-323"),
                             (1e20, b"100000000000000000000.0"), (1e21, b"1.0e+21"),
                             (sys.float_info.max, b"1.7976931348623157e+308")):
            expected = b"F" + len(token).to_bytes(8, "big") + token
            with self.subTest(value=value):
                self.assertEqual(encode_typed(value, "f64", {}), expected)

    def test_schema_validation_rejects_shape_and_range_mismatch(self):
        for value, schema in ((True, "i64"), (1, "bool"), ([1], {"tuple": ["i64", "i64"]}),
                              ({"x": 1}, {"record": "Missing"}), (1 << 63, "i64")):
            with self.subTest(value=value, schema=schema), self.assertRaises(ValueError):
                encode_typed(value, schema, {})
        min_schema = {"int_min": "-9223372036854775808"}
        max_schema = {"int_min": "9223372036854775807"}
        self.assertEqual(encode_typed(-(1 << 63), min_schema, {})[0:1], b"J")
        self.assertEqual(encode_typed((1 << 63) - 1, max_schema, {})[0:1], b"J")

    def test_schema_is_fully_validated_before_empty_or_absent_values(self):
        invalid = (
            ([], {"list": {"record": "Missing"}}, {}),
            ({"none": True}, {"optional": {"bogus": "i64"}}, {}),
            ([], {"list": ["i64"]}, {}),
            ([], {"map": [{"record": "Missing"}, "str"]}, {}),
            ({"none": 1}, {"optional": "i64"}, {}),
            ({"none": True}, {"optional": "i64"}, {"unused.Bad": {"kind": "alias", "type": {"named": "unused.Bad"}}}),
            ([], {"tuple": ["i64"]}, {}),
            ([], "null", {"record": {"kind": "record", "fields": {}}, "pkg.Bad": {"kind": "alias", "type": {"record": "missing.Type"}}}),
            (0, {"int_min": True}, {}),
            (1, {"int_min": 1}, {}),
            (1, {"int_min": "01"}, {}),
            (1, {"int_min": "-0"}, {}),
            (1, {"int_min": "9223372036854775808"}, {}),
            ("a", {"literal_set": ["b", "a"]}, {}),
            ("a", {"literal_set": ["a", "a"]}, {}),
            ([], {"full_map": ["pkg.NotEnum", "str"]}, {"pkg.NotEnum": {"kind": "record", "fields": {}}}),
            ([], {"full_map": ["pkg.Fielded", "str"]}, {"pkg.Fielded": {"kind": "variant", "cases": {"A": {"field": "i64"}}}}),
        )
        for value, schema, declarations in invalid:
            with self.subTest(schema=schema, declarations=declarations), self.assertRaises(ValueError):
                encode_typed(value, schema, declarations)

    def test_recursive_and_mutually_recursive_declared_records_resolve_by_name(self):
        self_ref = {"pkg.Node": {"kind": "record", "fields": {"next": {"optional": {"record": "pkg.Node"}}}}}
        value = {"next": {"none": True}}
        self.assertTrue(encode_typed(value, {"record": "pkg.Node"}, self_ref))
        mutual = {
            "pkg.Left": {"kind": "record", "fields": {"right": {"optional": {"record": "pkg.Right"}}}},
            "pkg.Right": {"kind": "record", "fields": {"left": {"optional": {"record": "pkg.Left"}}}},
        }
        nested = {"right": {"some": {"left": {"none": True}}}}
        self.assertTrue(encode_typed(nested, {"record": "pkg.Left"}, mutual))
        collision_name = {"record": {"kind": "record", "fields": {}},
                          "pkg.Bad": {"kind": "alias", "type": {"record": "Missing"}}}
        with self.assertRaises(ValueError): encode_typed(None, "null", collision_name)

    def test_manifest_canonical_bytes_and_contract_id_vector(self):
        manifest = {
            "alula_version": "0.29", "machine": "Example", "revision": 1,
            "types": {"aliases": [], "records": [], "variants": []},
            "parties": [], "signals": [], "queries": [],
            "codec": CODEC_PROJECTION, "event_envelope": ENVELOPE_PROJECTION,
        }
        expected = b'{"alula_version":"0.29","codec":{"digest":{"algorithm":"SHA-256","domain":"alula-value-digest","representation":"sha256:lowercase-hex-64","separator_hex":"00"},"domain":["alias","bool","f64","full_map","i64","id","int_min","list","literal_set","map","null","optional","record","str","tuple","variant"],"f64":{"finite":"shortest-roundtrip-decimal","fixed_exponent_max":20,"fixed_exponent_min":-6,"json_finite":"number-same-binary64","json_specials":"$float-tag","nan":"NaN","nan_payload":"discard","negative_infinity":"-Infinity","negative_zero":"-0.0","positive_infinity":"Infinity","positive_zero":"0.0","tie_break":"nearest-then-even"},"full_map":{"coverage":"all-cases-exactly-once","key_type":"fieldless-enum"},"i64":{"maximum":"9223372036854775807","minimum":"-9223372036854775808","wire":"canonical-decimal-json-string"},"int_min":{"bound":"inclusive-lower-bound","form":"int>=n"},"json":{"arrays":"preserve","bom":false,"duplicate_keys":"reject","encoding":"UTF-8","object_key_order":"Unicode code point","safe_integer_range":"-9007199254740992..9007199254740991","string_escaping":"JSON-short-escapes; other-U+0000-001F-lowercase-u00xx; slash-literal","unicode_normalization":"none","unknown_fields":"reject"},"literal_set":{"minimum_values":2,"order":"Unicode code point","unique":true},"type_forms":{"alias":"declared-name-wraps-base","bool":"json-boolean","f64":"json-number-or-float-tag","full_map":"array-of-all-enum-pairs","i64":"canonical-decimal-json-string","id":"lowercase-uuid-text","int_min":"canonical-decimal-json-string-with-lower-bound","list":"json-array-ordered","literal_set":"json-string-in-closed-set","map":"array-of-key-value-pairs","null":"json-null","optional":"none-some-object","record":"json-object-with-exact-fields","str":"json-string","tuple":"json-array-fixed-arity-at-least-two","variant":"case-fields-object"},"typed_bytes":{"f64":"length-prefixed-ASCII","length":"u64-big-endian","markers":{"alias":"Y","bool":"B","f64":"F","full_map":"G","i64":"I","id":"U","int_min":"J","list":"L","literal_set":"C","map":"M","null":"N","optional":"O","record":"R","str":"S","tuple":"T","variant":"V"},"text":"length-prefixed-UTF-8"}},"event_envelope":{"contract_binding":"contract_id-equals-instance-contract-pin","data":"object-selected-by-event-kind-schema","event_id":"logical-event-not-rpc-call","event_kinds":[{"conditional_fields":{"pause_id":"parent-continue-only","request_id":"parent-owned-control-only"},"data_shape":"control-data","name":"machine.control","required_fields":["signal"]},{"conditional_fields":{"gate_id":"gate-signal-only","subject_id":"subject-bound-gate-only"},"data_shape":"declared-signal-fields","name":"party.signal","required_fields":["party","signal"]},{"conditional_fields":{},"data_shape":"code-and-message","name":"request.failure","required_fields":["party","request_id"]},{"conditional_fields":{},"data_shape":"result-only","name":"request.reply","required_fields":["party","request_id"]}],"instance_id":"non-reusable","required_fields":["contract_id","data","event_id","event_kind","instance_id"],"unknown_fields":"reject"},"machine":"Example","parties":[],"queries":[],"revision":1,"signals":[],"types":{"aliases":[],"records":[],"variants":[]}}'
        self.assertEqual(canonical_manifest_bytes(manifest), expected)
        self.assertEqual(contract_id(manifest), "sha256:0f1ff7f8cfcb7541b8c3a72074ca2d1aea0b3fdeeb5d52dc81067947015f8792")
        reordered = dict(reversed(list(manifest.items())))
        self.assertEqual(contract_id(reordered), contract_id(manifest))
        for invalid in (None, {}, {**manifest, "contract_id": "self"}, {**manifest, "artifact_id": "build"},
                        {**manifest, "location": "file"}, {**manifest, "codec": "typed/bytes"},
                        {**manifest, "revision": 1 << 54}, {**manifest, "codec": {**manifest["codec"], "json": {}}},
                        {**manifest, "codec": {**manifest["codec"], "json": {**manifest["codec"]["json"], "bom": 0}}},
                        {**manifest, "codec": {**manifest["codec"], "json": {**manifest["codec"]["json"], "bom": 1}}},
                        {**manifest, "codec": {**manifest["codec"], "digest": {**manifest["codec"]["digest"], "algorithm": "MD5"}}},
                        {**manifest, "codec": {**manifest["codec"], "digest": {**manifest["codec"]["digest"], "separator_hex": "ff"}}},
                        {**manifest, "codec": {**manifest["codec"], "typed_bytes": {**manifest["codec"]["typed_bytes"], "markers": {**manifest["codec"]["typed_bytes"]["markers"], "i64": "Z"}}}},
                        {**manifest, "codec": {**manifest["codec"], "literal_set": {**manifest["codec"]["literal_set"], "minimum_values": 0}}},
                        {**manifest, "codec": {**manifest["codec"], "f64": {**manifest["codec"]["f64"], "negative_zero": "0.0"}}},
                        {**manifest, "event_envelope": {**manifest["event_envelope"], "event_id": "rpc-id"}}):
            before = copy.deepcopy(invalid)
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                canonical_manifest_bytes(invalid)
            self.assertEqual(invalid, before)
        with self.assertRaises(ValueError):
            parse_manifest_json('{"revision":0,"revision":1}')
        with self.assertRaises(ValueError):
            parse_manifest_json('{"revision":1.0}')
        machine_changed = {**manifest, "machine": "Example2"}
        self.assertNotEqual(contract_id(machine_changed), contract_id(manifest))

    def test_manifest_projection_resolves_and_covers_public_declarations(self):
        # Reuse the complete empty vector fixture, then add public declarations.
        base = {
            "alula_version": "0.29", "machine": "Example", "revision": 1,
            "types": {"aliases": [{"name": "pkg.Count", "type": "i64"}],
                      "records": [{"name": "pkg.Pair", "fields": [{"name": "left", "type": {"int_min": "0"}}, {"name": "right", "type": {"literal_set": ["a", "b"]}}]}],
                      "variants": [{"name": "pkg.Mode", "cases": [{"name": "A", "fields": []}, {"name": "B", "fields": []}]},
                                   {"name": "pkg.Result", "cases": [{"name": "Failed", "fields": [{"name": "reason", "type": "str"}]}, {"name": "Ok", "fields": [{"name": "count", "type": {"named": "pkg.Count"}}]}]}]},
            "parties": [{"name": "reviewer", "kind": "human", "inputs": [{"name": "prompt", "type": "str"}], "result": {"variant": "pkg.Result"}}],
            "signals": [{"name": "note", "party": "reviewer", "fields": [{"name": "content", "type": "str"}]}],
            "queries": [{"name": "status", "inputs": [{"name": "allowed", "type": {"full_map": ["pkg.Mode", "str"]}}], "result": "i64"}],
            "codec": CODEC_PROJECTION, "event_envelope": ENVELOPE_PROJECTION,
        }
        canonical = canonical_manifest_bytes(base)
        self.assertIn(b'"name":"pkg.Pair"', canonical)
        self.assertIn(b'"name":"note"', canonical)
        self.assertIn(b'"name":"status"', canonical)
        self.assertNotEqual(contract_id(base), "sha256:111162fa4580c3634a64f16dc3e49d4f1cc99a4646b1195abd22aab3cca432c0")
        unknown = {**base, "parties": [{**base["parties"][0], "artifact_id": "must-not-enter"}]}
        with self.assertRaises(ValueError): canonical_manifest_bytes(unknown)
        unresolved = {**base, "types": {**base["types"], "records": [{"name": "pkg.Pair", "fields": [{"name": "left", "type": {"record": "missing.Type"}}]}]}}
        with self.assertRaises(ValueError): canonical_manifest_bytes(unresolved)


if __name__ == "__main__":
    unittest.main()
