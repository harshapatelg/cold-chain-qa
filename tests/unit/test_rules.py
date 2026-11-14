"""
Unit tests for Business Rules and Risk Scoring Logic.

Tests:
1. Boundary condition tests for produce safe temperature limits.
2. Risk score duration accumulation from time series readings.
3. Risk level threshold transitions (OK -> WARNING -> CRITICAL).
4. Boundary cases loaded from data/boundary_cases.csv.
"""

import unittest
import csv
import os
from datetime import datetime, timezone, timedelta
from app.rules import is_outside_safe_range, calculate_risk_score, determine_risk_level


class TestRules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cls.csv_path = os.path.join(base_dir, "data", "boundary_cases.csv")
        cls.boundary_cases = []
        if os.path.exists(cls.csv_path):
            with open(cls.csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cls.boundary_cases.append(row)

    def test_temperature_limit_boundaries_from_csv(self):
        """Boundary Value Analysis: produce safe range checks (tomato [10.0, 15.0])."""
        cases = [c for c in self.boundary_cases if c["category"] == "produce_range_tomato"]
        self.assertGreater(len(cases), 0, "No produce_range_tomato test cases found in CSV")

        for row in cases:
            val = float(row["test_value"])
            min_c = float(row["min_limit"])
            max_c = float(row["max_limit"])
            expected_res = row["expected_result"].strip().upper()
            desc = row["description"]

            with self.subTest(msg=desc, temp=val, expected=expected_res):
                is_outside = is_outside_safe_range(val, min_c, max_c)
                if expected_res == "INSIDE":
                    self.assertFalse(is_outside, f"Expected {val} C to be INSIDE [{min_c}, {max_c}]")
                else:
                    self.assertTrue(is_outside, f"Expected {val} C to be OUTSIDE [{min_c}, {max_c}]")

    def test_risk_level_thresholds_from_csv(self):
        """Boundary Value Analysis: Risk level classification based on minutes outside range."""
        cases = [c for c in self.boundary_cases if c["category"] == "risk_level"]
        self.assertGreater(len(cases), 0, "No risk_level test cases found in CSV")

        for row in cases:
            minutes = float(row["test_value"])
            expected_lvl = row["expected_result"].strip().upper()
            desc = row["description"]

            with self.subTest(msg=desc, minutes=minutes, expected=expected_lvl):
                level = determine_risk_level(minutes)
                self.assertEqual(level, expected_lvl)

    def test_risk_level_negative_minutes_raises_error(self):
        """Negative testing: negative risk duration must raise ValueError."""
        with self.assertRaises(ValueError):
            determine_risk_level(-1.0)

    def test_calculate_risk_score_insufficient_readings(self):
        """Zero or single reading produces 0.0 risk score."""
        self.assertEqual(calculate_risk_score([], 10.0, 15.0), 0.0)
        single = [{"temperature_c": 25.0, "timestamp": datetime.now(timezone.utc)}]
        self.assertEqual(calculate_risk_score(single, 10.0, 15.0), 0.0)

    def test_calculate_risk_score_accumulation(self):
        """Accumulates duration when readings are outside safe range."""
        base_time = datetime(2026, 11, 14, 10, 0, 0, tzinfo=timezone.utc)
        # Tomato range: 10.0 to 15.0 C
        # t0: 12.0 C (safe)
        # t1 (+30 min): 18.0 C (outside -> adds 30 min)
        # t2 (+30 min): 14.0 C (safe -> adds 0 min)
        # t3 (+60 min): 20.0 C (outside -> adds 60 min)
        # Total outside = 90.0 min
        readings = [
            {"temperature_c": 12.0, "timestamp": base_time},
            {"temperature_c": 18.0, "timestamp": base_time + timedelta(minutes=30)},
            {"temperature_c": 14.0, "timestamp": base_time + timedelta(minutes=60)},
            {"temperature_c": 20.0, "timestamp": base_time + timedelta(minutes=120)},
        ]
        score = calculate_risk_score(readings, 10.0, 15.0)
        self.assertEqual(score, 90.0)
        level = determine_risk_level(score)
        self.assertEqual(level, "WARNING")

    def test_calculate_risk_score_with_iso_strings(self):
        """Correctly parses ISO string timestamps in readings."""
        readings = [
            {"temperature_c": 12.0, "timestamp": "2026-11-14T10:00:00+00:00"},
            {"temperature_c": 22.0, "timestamp": "2026-11-14T10:45:00+00:00"},
        ]
        score = calculate_risk_score(readings, 10.0, 15.0)
        self.assertEqual(score, 45.0)


if __name__ == "__main__":
    unittest.main()
