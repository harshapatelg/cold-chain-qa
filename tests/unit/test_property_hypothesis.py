"""
Property-Based Testing with Hypothesis for Cold-Chain Spoilage Service.

Tests 3 fundamental invariant properties:
1. Invariant 1: Risk score (cumulative minutes) is NEVER negative for any sequence
   of valid chronological or unordered sensor readings.
2. Invariant 2: Risk level is monotonically non-decreasing as cumulative minutes outside
   safe range increase (OK <= WARNING <= CRITICAL).
3. Invariant 3: Any temperature strictly outside the valid sensor range [-40.0, 60.0] C
   is ALWAYS rejected with ValueError.
"""

import unittest
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings
from app.rules import calculate_risk_score, determine_risk_level
from app.validators import validate_temperature


LEVEL_ORDER = {"OK": 1, "WARNING": 2, "CRITICAL": 3}


class TestPropertyHypothesis(unittest.TestCase):

    @settings(max_examples=100)
    @given(
        st.lists(
            st.tuples(
                st.floats(min_value=-40.0, max_value=60.0, allow_nan=False),
                st.integers(min_value=0, max_value=86400),
            ),
            min_size=0,
            max_size=20,
        ),
        st.floats(min_value=-20.0, max_value=30.0, allow_nan=False),
        st.floats(min_value=0.0, max_value=20.0, allow_nan=False),
    )
    def test_property_risk_score_never_negative(self, readings_data, base_temp, span):
        """
        Invariant 1: For any arbitrary sequence of temperature readings,
        the calculated cumulative risk score must never be negative.
        """
        min_temp = min(base_temp, base_temp + span)
        max_temp = max(base_temp, base_temp + span)

        base_dt = datetime(2026, 11, 14, 0, 0, 0, tzinfo=timezone.utc)
        readings = [
            {
                "temperature_c": temp,
                "timestamp": base_dt + timedelta(seconds=offset_sec),
            }
            for temp, offset_sec in readings_data
        ]

        score = calculate_risk_score(readings, min_temp, max_temp)
        self.assertGreaterEqual(score, 0.0, f"Risk score {score} was negative!")

    @settings(max_examples=100)
    @given(
        st.floats(min_value=0.0, max_value=500.0, allow_nan=False),
        st.floats(min_value=0.0, max_value=500.0, allow_nan=False),
    )
    def test_property_risk_level_monotonicity(self, m1, m2):
        """
        Invariant 2: Risk level is monotonically non-decreasing.
        If duration A <= duration B, then Severity(Level(A)) <= Severity(Level(B)).
        """
        smaller = min(m1, m2)
        larger = max(m1, m2)

        lvl_smaller = determine_risk_level(smaller)
        lvl_larger = determine_risk_level(larger)

        rank_smaller = LEVEL_ORDER[lvl_smaller]
        rank_larger = LEVEL_ORDER[lvl_larger]

        self.assertLessEqual(
            rank_smaller,
            rank_larger,
            f"Monotonicity violated: {smaller} min gave {lvl_smaller} (rank {rank_smaller}) "
            f"while {larger} min gave {lvl_larger} (rank {rank_larger})",
        )

    @settings(max_examples=100)
    @given(
        st.one_of(
            st.floats(min_value=-10000.0, max_value=-40.0001, allow_nan=False),
            st.floats(min_value=60.0001, max_value=10000.0, allow_nan=False),
        )
    )
    def test_property_invalid_temperatures_always_rejected(self, out_of_bounds_temp):
        """
        Invariant 3: Any temperature reading strictly outside [-40.0, 60.0] C
        is ALWAYS rejected with ValueError.
        """
        with self.assertRaises(ValueError):
            validate_temperature(out_of_bounds_temp)


if __name__ == "__main__":
    unittest.main()
