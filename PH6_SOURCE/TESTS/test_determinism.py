#!/usr/bin/env python3
"""
PH6CRAM State Invariant Validation Suite.
Enforces calculation immutability across updates.
PROPOSED artifact. Ratified_by: null.
"""

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from SENSORS.measurement_engine import evaluate_sensor_frame

BLAKE2B_EMPTY = hashlib.blake2b(b"", digest_size=32).hexdigest()
BLAKE2B_KNOWN = hashlib.blake2b(b"ph6-test-frame", digest_size=32).hexdigest()


class TestInstrumentDeterminism(unittest.TestCase):

    def setUp(self):
        self.mock_hash = BLAKE2B_KNOWN
        self.stable_metric = 55.4

    def test_absolute_id_and_hash_determinism(self):
        run_alpha = evaluate_sensor_frame(self.mock_hash, self.stable_metric)
        run_beta = evaluate_sensor_frame(self.mock_hash, self.stable_metric)
        self.assertEqual(run_alpha["measurement_id"], run_beta["measurement_id"])
        self.assertEqual(run_alpha["execution_hash"], run_beta["execution_hash"])

    def test_explicit_value_faults(self):
        with self.assertRaises(ValueError):
            evaluate_sensor_frame("INVALID_SHORT_HASH", 45.0)

    def test_pass_verdict_within_bounds(self):
        result = evaluate_sensor_frame(self.mock_hash, 50.0)
        self.assertEqual(result["verdict"], "PASS")

    def test_drop_verdict_below_bounds(self):
        result = evaluate_sensor_frame(self.mock_hash, 5.0)
        self.assertEqual(result["verdict"], "DROP")

    def test_drop_verdict_above_bounds(self):
        result = evaluate_sensor_frame(self.mock_hash, 99.0)
        self.assertEqual(result["verdict"], "DROP")

    def test_schema_id_constant(self):
        result = evaluate_sensor_frame(self.mock_hash, 42.0)
        self.assertEqual(result["schema_id"], "ph6.pseudo_measurement.v1")

    def test_hash_width_is_64(self):
        result = evaluate_sensor_frame(self.mock_hash, 42.0)
        self.assertEqual(len(result["measurement_id"]), 64)
        self.assertEqual(len(result["execution_hash"]), 64)

    def test_metric_value_preserved(self):
        result = evaluate_sensor_frame(self.mock_hash, 42.7)
        self.assertAlmostEqual(result["metric_value"], 42.7)

    def test_boundary_inclusive_lower(self):
        result = evaluate_sensor_frame(self.mock_hash, 12.5)
        self.assertEqual(result["verdict"], "PASS")

    def test_boundary_inclusive_upper(self):
        result = evaluate_sensor_frame(self.mock_hash, 87.2)
        self.assertEqual(result["verdict"], "PASS")

    def test_different_metrics_produce_different_ids(self):
        r1 = evaluate_sensor_frame(self.mock_hash, 30.0)
        r2 = evaluate_sensor_frame(self.mock_hash, 40.0)
        self.assertNotEqual(r1["measurement_id"], r2["measurement_id"])
        self.assertNotEqual(r1["execution_hash"], r2["execution_hash"])


if __name__ == "__main__":
    unittest.main()
