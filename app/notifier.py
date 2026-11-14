"""
Fake SMS Alert Gateway for Cold-Chain Notifications.

In production, this module would integrate with Twilio or an enterprise SMS
gateway. In this testing and QA project, it serves as an external dependency
designed to be verified and mocked using unittest.mock.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone


class SMSAlertGateway:
    """Simulated external SMS alert gateway for spoilage breach alerts."""

    def __init__(self, api_endpoint: str = "https://sms-gateway.internal.net/v1/send"):
        self.api_endpoint = api_endpoint
        self.sent_messages: List[Dict[str, Any]] = []

    def send_alert(self, phone: str, message: str) -> bool:
        """
        Sends an SMS alert to a cold-chain facility operator.
        
        Args:
            phone: Target phone number (e.g., '+15551234567').
            message: Alert text containing batch ID, risk level, and temperature breach.
            
        Returns:
            True if SMS was successfully dispatched, False otherwise.
        """
        if not phone or not phone.strip():
            raise ValueError("Phone number cannot be empty")
        if not message or not message.strip():
            raise ValueError("SMS message cannot be empty")

        # Record message record in memory for local verification
        record = {
            "phone": phone.strip(),
            "message": message.strip(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "DELIVERED",
        }
        self.sent_messages.append(record)
        return True


# Default gateway instance used by the service
notifier_gateway = SMSAlertGateway()


def send_spoilage_sms(batch_id: str, produce_type: str, risk_level: str, minutes_outside: float) -> bool:
    """Helper function to dispatch alert SMS via the gateway."""
    phone = "+1-555-0199"  # Default duty manager alert line
    message = (
        f"[COLD-CHAIN ALERT] Batch {batch_id} ({produce_type}) reached {risk_level} status! "
        f"Total duration outside safe range: {minutes_outside:.1f} minutes."
    )
    return notifier_gateway.send_alert(phone, message)
