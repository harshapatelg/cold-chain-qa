"""
In-Memory Storage for Cold-Chain Produce Spoilage Alert Service.

Stores registered produce safe ranges, batch readings, and generated alerts
in memory (no external database needed, per lab specifications). Thread-safe
operations and a clean reset function are provided for deterministic testing.
"""

from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timezone
import threading
from app.config import PRELOADED_PRODUCE_RANGES
from app.rules import calculate_risk_score, determine_risk_level
from app.notifier import send_spoilage_sms


class ColdChainStore:
    """Thread-safe in-memory store for batches, produce types, and alerts."""

    def __init__(self):
        self._lock = threading.Lock()
        self.produce_types: Dict[str, Tuple[float, float]] = {}
        self.batches: Dict[str, Dict[str, Any]] = {}
        self.alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_counter: int = 1
        self.reset()

    def reset(self):
        """Resets the store back to initial clean state with preloaded produce types."""
        with self._lock:
            self.produce_types = dict(PRELOADED_PRODUCE_RANGES)
            self.batches = {}
            self.alerts = {}
            self.alert_counter = 1

    def get_produce_type(self, name: str) -> Optional[Tuple[float, float]]:
        with self._lock:
            return self.produce_types.get(name.lower().strip())

    def get_all_produce_types(self) -> Dict[str, Tuple[float, float]]:
        with self._lock:
            return dict(self.produce_types)

    def register_produce_type(self, name: str, min_c: float, max_c: float) -> Tuple[float, float]:
        with self._lock:
            cleaned_name = name.lower().strip()
            self.produce_types[cleaned_name] = (min_c, max_c)
            return self.produce_types[cleaned_name]

    def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            batch = self.batches.get(batch_id)
            if not batch:
                return None
            return {
                "batch_id": batch["batch_id"],
                "produce_type": batch["produce_type"],
                "risk_score": batch["risk_score"],
                "risk_level": batch["risk_level"],
                "readings_count": len(batch["readings"]),
            }

    def record_reading(
        self,
        batch_id: str,
        produce_type: str,
        temperature_c: float,
        humidity_pct: float,
        timestamp_dt: datetime,
    ) -> Dict[str, Any]:
        """
        Records a validated reading for a produce batch.
        
        Rules:
        - Duplicate readings (same batch_id and timestamp) are ignored and do not alter state.
        - Updates cumulative risk score and risk level.
        - Automatically creates an alert and dispatches an SMS when risk level reaches
          WARNING or CRITICAL (if an active alert does not already exist).
        """
        ts_iso = timestamp_dt.isoformat()

        with self._lock:
            min_c, max_c = self.produce_types[produce_type]

            if batch_id not in self.batches:
                self.batches[batch_id] = {
                    "batch_id": batch_id,
                    "produce_type": produce_type,
                    "readings": [],
                    "seen_timestamps": set(),
                    "risk_score": 0.0,
                    "risk_level": "OK",
                    "highest_alerted_level": "OK",
                }

            batch = self.batches[batch_id]

            # Rule: duplicate reading (same batch and timestamp) is ignored
            if ts_iso in batch["seen_timestamps"]:
                return {
                    "status": "ignored",
                    "reason": "duplicate timestamp for batch",
                    "batch_id": batch_id,
                    "risk_score": batch["risk_score"],
                    "risk_level": batch["risk_level"],
                }

            # Add reading
            batch["readings"].append({
                "temperature_c": temperature_c,
                "humidity_pct": humidity_pct,
                "timestamp": timestamp_dt,
            })
            batch["seen_timestamps"].add(ts_iso)

            # Recalculate risk score & level
            risk_score = calculate_risk_score(batch["readings"], min_c, max_c)
            risk_level = determine_risk_level(risk_score)
            batch["risk_score"] = risk_score
            batch["risk_level"] = risk_level

            # Alert triggering logic
            if risk_level in ("WARNING", "CRITICAL") and batch["highest_alerted_level"] != risk_level:
                alert_id = f"ALT-{self.alert_counter:04d}"
                self.alert_counter += 1
                self.alerts[alert_id] = {
                    "alert_id": alert_id,
                    "batch_id": batch_id,
                    "produce_type": produce_type,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "status": "ACTIVE",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "acknowledged_at": None,
                }
                batch["highest_alerted_level"] = risk_level
                # Dispatch notification via SMS gateway
                send_spoilage_sms(batch_id, produce_type, risk_level, risk_score)

            return {
                "status": "accepted",
                "batch_id": batch_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
            }

    def list_alerts(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.alerts.values())

    def acknowledge_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            alert = self.alerts.get(alert_id)
            if not alert:
                return None
            alert["status"] = "ACKNOWLEDGED"
            alert["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            return dict(alert)


# Global store instance
store = ColdChainStore()
