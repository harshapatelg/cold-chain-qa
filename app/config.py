"""
Application Configuration and Preconfigured Assumptions.

This module defines all constants and business rules for the Cold-Chain
Produce Spoilage Alert Service. As required by the QA project guidelines,
all numerical assumptions are centralized here to allow easy tuning and
clear documentation.
"""

import os
from typing import Dict, Tuple

# Preloaded produce safe temperature ranges (min_c, max_c)
# Note: Readings exactly on range limits count as inside the safe range.
PRELOADED_PRODUCE_RANGES: Dict[str, Tuple[float, float]] = {
    "tomato": (10.0, 15.0),
    "leafy_greens": (0.0, 4.0),
    "mango": (10.0, 13.0),
}

# Physical sensor reading limits (Equivalence Partition boundaries)
SENSOR_TEMP_MIN_C: float = -40.0
SENSOR_TEMP_MAX_C: float = 60.0
SENSOR_HUMIDITY_MIN_PCT: float = 0.0
SENSOR_HUMIDITY_MAX_PCT: float = 100.0

# Spoilage risk level thresholds (cumulative minutes outside safe temperature range)
THRESHOLD_OK_MAX_MINUTES: float = 30.0       # < 30 min is OK
THRESHOLD_WARNING_MAX_MINUTES: float = 120.0  # 30 <= minutes < 120 is WARNING; >= 120 is CRITICAL

# Reading timestamp constraints
MAX_TIMESTAMP_AGE_SECONDS: int = 86400  # 24 hours
FUTURE_TIMESTAMP_TOLERANCE_SECONDS: int = 5  # Allow up to 5s clock skew

# Authentication configuration (PyJWT)
JWT_SECRET_KEY: str = "cold-chain-secret-key-ise2501-ca3-2026"
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRATION_SECONDS: int = 3600  # 1 hour

# Hardcoded demo user credentials for testing & lab evaluation
DEMO_USERS = {
    "operator_alice": "securepass123",
    "manager_bob": "coldchain2026",
}


def is_defect_active(defect_id: int) -> bool:
    """
    Checks if a deliberate seeded defect is active via the SEED_DEFECTS env var.
    
    Example:
        SEED_DEFECTS="1,2,3" enables Defects 1, 2, and 3.
        Unset or empty enables NO defects (production correct code).
    """
    seeded_env = os.environ.get("SEED_DEFECTS", "").strip()
    if not seeded_env:
        return False
    active_ids = [item.strip() for item in seeded_env.split(",") if item.strip()]
    return str(defect_id) in active_ids
