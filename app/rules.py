"""
Pure Business Rules for Cold-Chain Produce Spoilage & Risk Scoring.

This module contains pure, deterministic functions without any side-effects
or database dependencies:
1. is_outside_safe_range: checks if a temperature reading breaches boundaries.
2. calculate_risk_score: calculates cumulative minutes spent outside safe range.
3. determine_risk_level: assigns "OK", "WARNING", or "CRITICAL" based on minutes.
"""

from datetime import datetime
from typing import List, Dict, Any
from app.config import (
    THRESHOLD_OK_MAX_MINUTES,
    THRESHOLD_WARNING_MAX_MINUTES,
    is_defect_active,
)


def is_outside_safe_range(temperature_c: float, min_temp_c: float, max_temp_c: float) -> bool:
    """
    Determines if a temperature reading is outside the safe range.
    Rule: A reading exactly on a range limit counts as INSIDE the safe range.
    
    Seeded Defect 2 (Off-by-one at boundary limit):
    When active, uses '<=' instead of '<' for the minimum temperature limit,
    causing readings exactly on the lower boundary to be incorrectly flagged
    as outside the safe range.
    """
    if is_defect_active(2):
        # SEEDED DEFECT #2: Off-by-one bug at lower boundary
        return (temperature_c <= min_temp_c) or (temperature_c > max_temp_c)

    # Correct logic: Exactly on range limits is INSIDE safe range
    return (temperature_c < min_temp_c) or (temperature_c > max_temp_c)


def calculate_risk_score(readings: List[Dict[str, Any]], min_temp_c: float, max_temp_c: float) -> float:
    """
    Calculates the total risk score (minutes spent outside safe range).
    
    Readings must be chronologically ordered. For each time interval between
    consecutive readings, if the reading at the interval was outside the safe range,
    the duration (in minutes) is added to the risk score.
    """
    if not readings or len(readings) < 2:
        return 0.0

    # Ensure chronologically sorted by timestamp
    sorted_readings = sorted(readings, key=lambda r: r["timestamp"])
    total_minutes_outside: float = 0.0

    for i in range(1, len(sorted_readings)):
        prev_r = sorted_readings[i - 1]
        curr_r = sorted_readings[i]

        # Calculate time delta in minutes
        t_prev = prev_r["timestamp"]
        t_curr = curr_r["timestamp"]
        if isinstance(t_prev, str):
            t_prev = datetime.fromisoformat(t_prev)
        if isinstance(t_curr, str):
            t_curr = datetime.fromisoformat(t_curr)

        delta_minutes = (t_curr - t_prev).total_seconds() / 60.0

        if delta_minutes < 0:
            # Out-of-order timestamps should not produce negative duration
            continue

        # If current reading is outside safe range, accumulate interval
        if is_outside_safe_range(curr_r["temperature_c"], min_temp_c, max_temp_c):
            total_minutes_outside += delta_minutes

    return round(total_minutes_outside, 2)


def determine_risk_level(minutes_outside_range: float) -> str:
    """
    Assigns spoilage risk level based on cumulative minutes outside safe range.
    - OK: below 30 minutes (< 30)
    - WARNING: 30 minutes up to 120 minutes (>= 30 and < 120)
    - CRITICAL: 120 minutes and above (>= 120)
    
    Seeded Defect 1 (Wrong threshold at exactly 30 minutes):
    When active, WARNING starts at '> 30' instead of '>= 30', meaning at exactly
    30.0 minutes it incorrectly returns 'OK' instead of 'WARNING'.
    """
    if minutes_outside_range < 0:
        raise ValueError("Risk score cannot be negative")

    if is_defect_active(1):
        # SEEDED DEFECT #1: Wrong boundary operator (<= instead of <)
        if minutes_outside_range <= THRESHOLD_OK_MAX_MINUTES:
            return "OK"
        elif minutes_outside_range < THRESHOLD_WARNING_MAX_MINUTES:
            return "WARNING"
        else:
            return "CRITICAL"

    # Correct logic:
    if minutes_outside_range < THRESHOLD_OK_MAX_MINUTES:
        return "OK"
    elif minutes_outside_range < THRESHOLD_WARNING_MAX_MINUTES:
        return "WARNING"
    else:
        return "CRITICAL"
