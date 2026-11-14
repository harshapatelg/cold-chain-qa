"""
Unit / Integration tests for FastAPI endpoints using TestClient.

Tests:
1. POST /login: valid and invalid credentials.
2. POST /produce: authentication, safe ranges, 422 for invalid bounds.
3. POST /readings: telemetry ingest, 422 for invalid sensors, duplicate reading ignore.
4. GET /batches/{batch_id}/status: 404 for unknown batches, status calculation.
5. GET /alerts and POST /alerts/{alert_id}/ack: alert dispatch and acknowledgment.
6. State immutability on failed requests.
"""

import unittest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.store import store


class TestApiEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        store.reset()

    def _get_auth_token(self, username="operator_alice", password="securepass123") -> str:
        res = self.client.post("/login", json={"username": username, "password": password})
        self.assertEqual(res.status_code, 200)
        return res.json()["access_token"]

    def test_health_check(self):
        """Root health check returns HEALTHY status."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "HEALTHY")

    def test_login_success_and_failure(self):
        """Tests login authentication with valid and invalid credentials."""
        # Success
        res_ok = self.client.post("/login", json={"username": "operator_alice", "password": "securepass123"})
        self.assertEqual(res_ok.status_code, 200)
        self.assertIn("access_token", res_ok.json())

        # Invalid password
        res_bad = self.client.post("/login", json={"username": "operator_alice", "password": "wrongpassword"})
        self.assertEqual(res_bad.status_code, 401)

        # Unknown user
        res_unknown = self.client.post("/login", json={"username": "hacker", "password": "nopassword"})
        self.assertEqual(res_unknown.status_code, 401)

    def test_endpoints_require_authentication(self):
        """All protected endpoints return 401 when Authorization header is missing."""
        endpoints = [
            ("POST", "/produce", {"name": "berry", "min_temp_c": 1.0, "max_temp_c": 3.0}),
            ("POST", "/readings", {"batch_id": "B1", "produce_type": "tomato", "temperature_c": 12.0, "humidity_pct": 50.0, "timestamp": datetime.now(timezone.utc).isoformat()}),
            ("GET", "/batches/B1/status", None),
            ("GET", "/alerts", None),
            ("POST", "/alerts/ALT-0001/ack", None),
        ]
        for method, path, payload in endpoints:
            with self.subTest(method=method, path=path):
                if method == "POST":
                    res = self.client.post(path, json=payload)
                else:
                    res = self.client.get(path)
                self.assertEqual(res.status_code, 401, f"Endpoint {path} did not enforce 401 authentication")

    def test_register_produce_type(self):
        """Registers a custom produce type with valid range."""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Valid registration
        res = self.client.post(
            "/produce",
            headers=headers,
            json={"name": "strawberry", "min_temp_c": 1.0, "max_temp_c": 4.0},
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["name"], "strawberry")
        self.assertEqual(data["min_temp_c"], 1.0)
        self.assertEqual(data["max_temp_c"], 4.0)

        # Invalid range (min > max) -> 422
        res_inv = self.client.post(
            "/produce",
            headers=headers,
            json={"name": "strawberry", "min_temp_c": 10.0, "max_temp_c": 2.0},
        )
        self.assertEqual(res_inv.status_code, 422)

    def test_submit_reading_validation_errors(self):
        """Rejects out-of-range sensor values, unknown produce types, and future timestamps."""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        now_iso = datetime.now(timezone.utc).isoformat()

        # Unknown produce type -> 422
        res1 = self.client.post(
            "/readings",
            headers=headers,
            json={"batch_id": "B-01", "produce_type": "unknown_fruit", "temperature_c": 12.0, "humidity_pct": 50.0, "timestamp": now_iso},
        )
        self.assertEqual(res1.status_code, 422)

        # Temperature out of sensor bounds -> 422
        res2 = self.client.post(
            "/readings",
            headers=headers,
            json={"batch_id": "B-01", "produce_type": "tomato", "temperature_c": 99.0, "humidity_pct": 50.0, "timestamp": now_iso},
        )
        self.assertEqual(res2.status_code, 422)

        # Humidity out of sensor bounds -> 422
        res3 = self.client.post(
            "/readings",
            headers=headers,
            json={"batch_id": "B-01", "produce_type": "tomato", "temperature_c": 12.0, "humidity_pct": 150.0, "timestamp": now_iso},
        )
        self.assertEqual(res3.status_code, 422)

        # Future timestamp -> 422
        future_iso = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        res4 = self.client.post(
            "/readings",
            headers=headers,
            json={"batch_id": "B-01", "produce_type": "tomato", "temperature_c": 12.0, "humidity_pct": 50.0, "timestamp": future_iso},
        )
        self.assertEqual(res4.status_code, 422)

    def test_duplicate_readings_ignored_and_state_preserved(self):
        """Duplicate reading for the same batch and timestamp is ignored."""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        ts = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()

        payload = {
            "batch_id": "BATCH-DUP-01",
            "produce_type": "tomato",
            "temperature_c": 12.0,
            "humidity_pct": 50.0,
            "timestamp": ts,
        }

        # First post -> accepted
        res1 = self.client.post("/readings", headers=headers, json=payload)
        self.assertEqual(res1.status_code, 201)
        self.assertEqual(res1.json()["status"], "accepted")

        # Second post with identical timestamp -> ignored
        res2 = self.client.post("/readings", headers=headers, json=payload)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["status"], "ignored")

        # Check readings count remains 1
        res_status = self.client.get("/batches/BATCH-DUP-01/status", headers=headers)
        self.assertEqual(res_status.status_code, 200)
        self.assertEqual(res_status.json()["readings_count"], 1)

    def test_failed_requests_do_not_change_stored_state(self):
        """Failed requests must leave stored state untouched."""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Initially, batch does not exist
        res_pre = self.client.get("/batches/BATCH-FAIL-CHECK/status", headers=headers)
        self.assertEqual(res_pre.status_code, 404)

        # Submit an invalid reading
        res_fail = self.client.post(
            "/readings",
            headers=headers,
            json={"batch_id": "BATCH-FAIL-CHECK", "produce_type": "tomato", "temperature_c": 999.0, "humidity_pct": 50.0, "timestamp": datetime.now(timezone.utc).isoformat()},
        )
        self.assertEqual(res_fail.status_code, 422)

        # Batch must still not exist
        res_post = self.client.get("/batches/BATCH-FAIL-CHECK/status", headers=headers)
        self.assertEqual(res_post.status_code, 404)

    def test_batch_risk_and_alert_lifecycle(self):
        """Submitting out-of-range readings triggers alert, and operator can acknowledge it."""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        base_time = datetime.now(timezone.utc) - timedelta(hours=2)

        # Reading 1: within range
        self.client.post("/readings", headers=headers, json={
            "batch_id": "BATCH-LIFECYCLE-1",
            "produce_type": "tomato",
            "temperature_c": 12.0,
            "humidity_pct": 60.0,
            "timestamp": base_time.isoformat(),
        })

        # Reading 2: 45 minutes later, temperature 22.0 C (outside safe range 10-15 C)
        # Should breach 30 min -> WARNING alert generated!
        res2 = self.client.post("/readings", headers=headers, json={
            "batch_id": "BATCH-LIFECYCLE-1",
            "produce_type": "tomato",
            "temperature_c": 22.0,
            "humidity_pct": 60.0,
            "timestamp": (base_time + timedelta(minutes=45)).isoformat(),
        })
        self.assertEqual(res2.status_code, 201)
        self.assertEqual(res2.json()["risk_level"], "WARNING")

        # Check batch status
        res_batch = self.client.get("/batches/BATCH-LIFECYCLE-1/status", headers=headers)
        self.assertEqual(res_batch.status_code, 200)
        self.assertEqual(res_batch.json()["risk_score"], 45.0)
        self.assertEqual(res_batch.json()["risk_level"], "WARNING")

        # Check alerts list
        res_alerts = self.client.get("/alerts", headers=headers)
        self.assertEqual(res_alerts.status_code, 200)
        alerts = res_alerts.json()["alerts"]
        self.assertGreater(len(alerts), 0)
        alert_id = alerts[0]["alert_id"]
        self.assertEqual(alerts[0]["status"], "ACTIVE")

        # Acknowledge alert
        res_ack = self.client.post(f"/alerts/{alert_id}/ack", headers=headers)
        self.assertEqual(res_ack.status_code, 200)
        self.assertEqual(res_ack.json()["status"], "acknowledged")
        self.assertEqual(res_ack.json()["alert"]["status"], "ACKNOWLEDGED")


    def test_produce_registration_empty_name(self):
        """Rejects empty produce name with 400 Bad Request."""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        res = self.client.post("/produce", headers=headers, json={"name": "   ", "min_temp_c": 1.0, "max_temp_c": 5.0})
        self.assertEqual(res.status_code, 400)

    def test_acknowledge_unknown_alert_returns_404(self):
        """Acknowledging a non-existent alert ID returns 404 Not Found."""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        res = self.client.post("/alerts/ALT-NONEXISTENT/ack", headers=headers)
        self.assertEqual(res.status_code, 404)

    def test_submit_reading_invalid_types_returns_400(self):
        """Non-numeric sensor readings or malformed types return 400 Bad Request."""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        # String instead of float for temperature
        res1 = self.client.post(
            "/readings",
            headers=headers,
            json={"batch_id": "B-BAD-TYPE", "produce_type": "tomato", "temperature_c": "hot", "humidity_pct": 50.0, "timestamp": datetime.now(timezone.utc).isoformat()},
        )
        self.assertEqual(res1.status_code, 400)

        # Boolean for humidity
        res2 = self.client.post(
            "/readings",
            headers=headers,
            json={"batch_id": "B-BAD-TYPE", "produce_type": "tomato", "temperature_c": 12.0, "humidity_pct": True, "timestamp": datetime.now(timezone.utc).isoformat()},
        )
        self.assertEqual(res2.status_code, 400)


if __name__ == "__main__":
    unittest.main()
