"""Executable probes for selected typed-digest rules; not runtime codec conformance."""

from __future__ import annotations

import json
import math
import struct
import sys
import unittest

from event_protocol_model import _freeze


class ValueCodecContractTests(unittest.TestCase):
    def test_signed_zero_has_distinct_typed_digest(self):
        self.assertNotEqual(_freeze(-0.0), _freeze(0.0))

    def test_equivalent_f64_number_spellings_have_same_digest_after_typed_parse(self):
        decoded = [float(json.loads(token)) for token in ("1", "1.0", "1e0")]
        self.assertEqual(_freeze(decoded[0]), _freeze(decoded[1]))
        self.assertEqual(_freeze(decoded[1]), _freeze(decoded[2]))

    def test_finite_binary64_json_roundtrip_at_edges_and_neighbors(self):
        values = (
            5e-324,
            math.nextafter(5e-324, math.inf),
            math.nextafter(1.0, 0.0),
            1.0,
            math.nextafter(1.0, math.inf),
            math.nextafter(sys.float_info.max, 0.0),
            sys.float_info.max,
            -0.0,
        )
        for value in values:
            with self.subTest(value=value):
                encoded = json.dumps(value, allow_nan=False)
                decoded = json.loads(encoded)
                self.assertEqual(struct.pack(">d", value), struct.pack(">d", decoded))

    def test_nan_payload_is_not_part_of_typed_digest(self):
        nan_a = struct.unpack(">d", bytes.fromhex("7ff8000000000001"))[0]
        nan_b = struct.unpack(">d", bytes.fromhex("7ff8000000000002"))[0]
        self.assertNotEqual(struct.pack(">d", nan_a), struct.pack(">d", nan_b))
        self.assertEqual(_freeze(nan_a), _freeze(nan_b))

    def test_infinity_sign_is_part_of_typed_digest(self):
        self.assertNotEqual(_freeze(math.inf), _freeze(-math.inf))


if __name__ == "__main__":
    unittest.main()
