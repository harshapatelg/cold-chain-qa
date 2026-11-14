"""
Pure Input Validators for Cold-Chain Data.

Validates sensor readings, produce definitions, and timestamps against
system constraints and equivalence classes. All functions are pure, raising
ValueError or TypeError upon rule violation so the API layer can map them
cleanly to HTTP 422 (Unprocessable Entity) or HTTP 400 (Bad Request).
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Tuple
from app.config import (
    SENSOR_TEMP_MIN_C,
    SENSOR_TEMP_MAX_C,
    SENSOR_HUMIDITY_MIN_PCT,
    SENSOR_HUMIDITY_MAX_PCT,
    MAX_TIMESTAMP_AGE_SECONDS,
    FUTURE_TIMESTAMP_TOLERANCE_SECONDS,
)


def validate_temperature(temp: Any) -> float:
    """
    Validates physical sensor temperature reading.
    Must be a number within [-40.0, 60.0] C.
    """
    if isinstance(temp, bool) or not isinstance(temp, (int, float)):
        raise TypeError(f"Temperature must be a number, received: {type(temp).__name__}")
    
    temp_float = float(temp)
    if temp_float < SENSOR_TEMP_MIN_C or temp_float > SENSOR_TEMP_MAX_C:
        raise ValueError(
            f"Temperature {temp_float} C is outside valid sensor range "
            f"[{SENSOR_TEMP_MIN_C}, {SENSOR_TEMP_MAX_C}] C"
        )
    return temp_float


def validate_humidity(humidity: Any) -> float:
    """
    Validates physical sensor relative humidity reading.
    Must be a number within [0.0, 100.0] %.
    """
    if isinstance(humidity, bool) or not isinstance(humidity, (int, float)):
        raise TypeError(f"Humidity must be a number, received: {type(humidity).__name__}")
    
    hum_float = float(humidity)
    if hum_float < SENSOR_HUMIDITY_MIN_PCT or hum_float > SENSOR_HUMIDITY_MAX_PCT:
        raise ValueError(
            f"Humidity {hum_float}% is outside valid sensor range "
            f"[{SENSOR_HUMIDITY_MIN_PCT}, {SENSOR_HUMIDITY_MAX_PCT}]%"
        )
    return hum_float


def validate_produce_range(min_temp: Any, max_temp: Any) -> Tuple[float, float]:
    """
    Validates safe temperature range for a produce type.
    Ensures min_temp <= max_temp and both are within valid sensor boundaries.
    """
    min_val = validate_temperature(min_temp)
    max_val = validate_temperature(max_temp)
    if min_val > max_val:
        raise ValueError(f"Minimum temperature ({min_val}) cannot be greater than maximum ({max_val})")
    return min_val, max_val


def validate_produce_type(produce_type: Any, registered_types: dict) -> str:
    """
    Validates that a produce type name exists in registered produce types.
    """
    if not isinstance(produce_type, str) or not produce_type.strip():
        raise TypeError("Produce type must be a non-empty string")
    name = produce_type.strip().lower()
    if name not in registered_types:
        raise ValueError(f"Unknown produce type: '{name}'. Registered: {list(registered_types.keys())}")
    return name


def validate_batch_id(batch_id: Any) -> str:
    """
    Validates batch ID identifier.
    """
    if not isinstance(batch_id, str) or not batch_id.strip():
        raise ValueError("Batch ID must be a non-empty string")
    return batch_id.strip()


def validate_timestamp(ts_input: Any, reference_time: datetime = None) -> datetime:
    """
    Validates sensor reading timestamp.
    Constraints:
    1. Must be a valid ISO 8601 string or datetime object.
    2. Cannot be older than 24 hours.
    3. Cannot be in the future (with a small 5-second tolerance for clock skew).
    """
    if isinstance(ts_input, datetime):
        dt = ts_input
    elif isinstance(ts_input, str):
        try:
            # Handle ISO format with Z or timezone offsets
            clean_str = ts_input.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
        except Exception as e:
            raise ValueError(f"Invalid timestamp format '{ts_input}': must be ISO-8601") from e
    else:
        raise TypeError(f"Timestamp must be a string or datetime, received: {type(ts_input).__name__}")

    # Ensure timezone-aware for comparison (normalize to UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    now = reference_time.astimezone(timezone.utc) if reference_time else datetime.now(timezone.utc)

    # Check future timestamp
    future_limit = now + timedelta(seconds=FUTURE_TIMESTAMP_TOLERANCE_SECONDS)
    if dt > future_limit:
        raise ValueError(f"Timestamp {dt.isoformat()} cannot be in the future (current: {now.isoformat()})")

    # Check older than 24 hours
    old_limit = now - timedelta(seconds=MAX_TIMESTAMP_AGE_SECONDS)
    if dt < old_limit:
        raise ValueError(f"Timestamp {dt.isoformat()} is older than 24 hours limit")

    return dt
