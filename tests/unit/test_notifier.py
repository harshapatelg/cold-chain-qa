"""
Unit tests for Fake SMS Alert Gateway and Notification Mocking.

Demonstrates unittest.mock usage for external alert services:
1. Unit tests for SMSAlertGateway business logic.
2. Mocking SMSAlertGateway.send_alert to test service isolation.
3. Asserting dispatch parameters, message formats, and call counts.
"""

import unittest
from unittest.mock import patch, MagicMock
from app.notifier import SMSAlertGateway, send_spoilage_sms


class TestNotifier(unittest.TestCase):

    def setUp(self):
        self.gateway = SMSAlertGateway()

    def test_send_alert_success(self):
        """SMSAlertGateway successfully logs and sends alert message."""
        result = self.gateway.send_alert("+15551234567", "Temperature breach detected in Batch A")
        self.assertTrue(result)
        self.assertEqual(len(self.gateway.sent_messages), 1)
        record = self.gateway.sent_messages[0]
        self.assertEqual(record["phone"], "+15551234567")
        self.assertEqual(record["message"], "Temperature breach detected in Batch A")
        self.assertEqual(record["status"], "DELIVERED")

    def test_send_alert_validates_inputs(self):
        """Rejects empty phone number or empty message with ValueError."""
        with self.assertRaises(ValueError):
            self.gateway.send_alert("", "Alert text")
        with self.assertRaises(ValueError):
            self.gateway.send_alert("  ", "Alert text")
        with self.assertRaises(ValueError):
            self.gateway.send_alert("+15551234567", "")
        with self.assertRaises(ValueError):
            self.gateway.send_alert("+15551234567", "   ")

    @patch("app.notifier.notifier_gateway.send_alert")
    def test_send_spoilage_sms_mocked(self, mock_send):
        """
        Demonstrates unittest.mock: Mocks the gateway to verify payload
        and ensure no external SMS is dispatched during unit testing.
        """
        mock_send.return_value = True

        result = send_spoilage_sms(
            batch_id="BATCH-TEST-01",
            produce_type="tomato",
            risk_level="WARNING",
            minutes_outside=45.5,
        )

        self.assertTrue(result)
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        phone_arg, message_arg = args[0], args[1]
        self.assertEqual(phone_arg, "+1-555-0199")
        self.assertIn("BATCH-TEST-01", message_arg)
        self.assertIn("WARNING", message_arg)
        self.assertIn("45.5 minutes", message_arg)

    @patch("app.notifier.notifier_gateway.send_alert")
    def test_send_spoilage_sms_gateway_failure_handling(self, mock_send):
        """Verifies resilience when external SMS gateway throws an exception."""
        mock_send.side_effect = RuntimeError("SMS Provider Connection Timeout")

        with self.assertRaises(RuntimeError) as ctx:
            send_spoilage_sms(
                batch_id="BATCH-TEST-ERR",
                produce_type="leafy_greens",
                risk_level="CRITICAL",
                minutes_outside=130.0,
            )
        self.assertIn("SMS Provider Connection Timeout", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
