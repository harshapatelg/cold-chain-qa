"""
Unit tests for Pure Input Validators (Boundary Value Analysis & Equivalence Partitioning).

Tests:
1. Boundary value tests loaded dynamically from data/boundary_cases.csv using subTest.
2. Equivalence class partitions for valid/invalid temperatures and humidities.
3. Negative and type safety tests (booleans, strings, None).
4. Timestamp age window (24 hours past, future rejection, clock skew tolerance).
5. Produce range integrity (min <= max).
"""

import unittest
import csv
import os
from datetime import datetime, timezone, timedelta
from app.validators import (
    validate_temperature,
    validate_humidity,
    validate_produce_range,
    validate_produce_type,
    validate_batch_id,
    validate_timestamp,
)


class TestValidators(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Locate and load data/boundary_cases.csv
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cls.csv_path = os.path.join(base_dir, "data", "boundary_cases.csv")
        cls.boundary_cases = []
        if os.path.exists(cls.csv_path):
            with open(cls.csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cls.boundary_cases.append(row)

    def test_temperature_boundary_cases_from_csv(self):
        """Boundary Value Analysis: Sensor temperature limits from CSV."""
        temp_cases = [c for c in self.boundary_cases if c["category"] == "sensor_temp"]
        self.assertGreater(len(temp_cases), 0, "No sensor_temp test cases found in CSV")

        for row in temp_cases:
            val = float(row["test_value"])
            is_valid = row["expected_valid"].strip().lower() == "true"
            desc = row["description"]

            with self.subTest(msg=desc, value=val, expected_valid=is_valid):
                if is_valid:
                    result = validate_temperature(val)
                    self.assertEqual(result, val)
                else:
                    with self.assertRaises(ValueError):
                        validate_temperature(val)

    def test_humidity_boundary_cases_from_csv(self):
        """Boundary Value Analysis: Sensor humidity limits from CSV."""
        hum_cases = [c for c in self.boundary_cases if c["category"] == "sensor_humidity"]
        self.assertGreater(len(hum_cases), 0, "No sensor_humidity test cases found in CSV")

        for row in hum_cases:
            val = float(row["test_value"])
            is_valid = row["expected_valid"].strip().lower() == "true"
            desc = row["description"]

            with self.subTest(msg=desc, value=val, expected_valid=is_valid):
                if is_valid:
                    result = validate_humidity(val)
                    self.assertEqual(result, val)
                else:
                    with self.assertRaises(ValueError):
                        validate_humidity(val)

    def test_temperature_type_safety(self):
        """Negative testing: boolean, non-numeric strings, and None must raise TypeError."""
        invalid_types = [True, False, "25.0", None, [], {}, (10,)]
        for item in invalid_types:
            with self.subTest(item=item, item_type=type(item).__name__):
                with self.assertRaises(TypeError):
                    validate_temperature(item)

    def test_humidity_type_safety(self):
        """Negative testing: boolean, non-numeric strings, and None must raise TypeError."""
        invalid_types = [True, False, "80.0", None, [50], {"hum": 50}]
        for item in invalid_types:
            with self.subTest(item=item, item_type=type(item).__name__):
                with self.assertRaises(TypeError):
                    validate_humidity(item)

    def test_produce_range_validation(self):
        """Equivalence partitioning: valid range vs min > max."""
        # Valid cases
        min_c, max_c = validate_produce_range(10.0, 15.0)
        self.assertEqual(min_c, 10.0)
        self.assertEqual(max_c, 15.0)

        # Equal min and max is valid
        min_c, max_c = validate_produce_range(4.0, 4.0)
        self.assertEqual(min_c, 4.0)
        self.assertEqual(max_c, 4.0)

        # min > max raises ValueError
        with self.assertRaises(ValueError):
            validate_produce_range(15.0, 10.0)

        # Out-of-sensor range raises ValueError
        with self.assertRaises(ValueError):
            validate_produce_range(-50.0, 10.0)
        with self.assertRaises(ValueError):
            validate_produce_range(10.0, 70.0)

    def test_produce_type_catalog_validation(self):
        """Catalog check: registered produce types accepted, unregistered rejected."""
        registered = {"tomato": (10.0, 15.0), "mango": (10.0, 13.0)}
        self.assertEqual(validate_produce_type("tomato", registered), "tomato")
        self.assertEqual(validate_produce_type("  TOMATO  ", registered), "tomato")

        with self.assertRaises(ValueError):
            validate_produce_type("banana", registered)
        with self.assertRaises(TypeError):
            validate_produce_type("", registered)
        with self.assertRaises(TypeError):
            validate_produce_type(123, registered)

    def test_batch_id_validation(self):
        """Batch ID must be non-empty string."""
        self.assertEqual(validate_batch_id("BATCH-001"), "BATCH-001")
        self.assertEqual(validate_batch_id("  BATCH-99  "), "BATCH-99")

        with self.assertRaises(ValueError):
            validate_batch_id("")
        with self.assertRaises(ValueError):
            validate_batch_id("   ")
        with self.assertRaises(ValueError):
            validate_batch_id(None)
        with self.assertRaises(ValueError):
            validate_batch_id(12345)

    def test_timestamp_validation_valid(self):
        """Accepts valid ISO-8601 strings within 24-hour window."""
        now = datetime.now(timezone.utc)
        valid_iso = now.isoformat()
        dt = validate_timestamp(valid_iso, reference_time=now)
        self.assertIsInstance(dt, datetime)

        # Timestamp 1 hour ago
        one_hour_ago = (now - timedelta(hours=1)).isoformat()
        dt_hour = validate_timestamp(one_hour_ago, reference_time=now)
        self.assertIsInstance(dt_hour, datetime)

        # Accepts datetime object directly
        dt_direct = validate_timestamp(now, reference_time=now)
        self.assertEqual(dt_direct, now)

    def test_timestamp_validation_rejects_future(self):
        """Rejects future timestamps beyond tolerance."""
        now = datetime.now(timezone.utc)
        # 1 minute in the future
        future_ts = (now + timedelta(minutes=1)).isoformat()
        with self.assertRaises(ValueError):
            validate_timestamp(future_ts, reference_time=now)

    def test_timestamp_validation_clock_skew_tolerance(self):
        """Allows up to 5 seconds of clock skew."""
        now = datetime.now(timezone.utc)
        slight_future = (now + timedelta(seconds=3)).isoformat()
        # Should not raise
        dt = validate_timestamp(slight_future, reference_time=now)
        self.assertIsInstance(dt, datetime)

    def test_timestamp_validation_rejects_older_than_24h(self):
        """Rejects readings older than 24 hours."""
        now = datetime.now(timezone.utc)
        old_ts = (now - timedelta(hours=24, minutes=1)).isoformat()
        with self.assertRaises(ValueError):
            validate_timestamp(old_ts, reference_time=now)

    def test_timestamp_validation_malformed(self):
        """Rejects malformed strings and invalid data types."""
        with self.assertRaises(ValueError):
            validate_timestamp("not-a-timestamp")
        with self.assertRaises(TypeError):
            validate_timestamp(1609459200)


if __name__ == "__main__":
    unittest.main()
