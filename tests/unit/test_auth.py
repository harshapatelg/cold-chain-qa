"""
Unit tests for Authentication and JWT Security (PyJWT).

Tests:
1. User credential authentication against demo accounts.
2. Token generation and claims encoding.
3. Signature verification and payload decoding.
4. Tampered token rejection.
5. Expired token rejection.
6. require_auth dependency enforcement for HTTP 401.
"""

import unittest
from datetime import timedelta
from unittest.mock import MagicMock
import jwt
from fastapi import HTTPException
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM
from app.auth import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    require_auth,
)


class TestAuth(unittest.TestCase):

    def test_authenticate_user_success(self):
        """Validates credentials for operator_alice and manager_bob."""
        self.assertTrue(authenticate_user("operator_alice", "securepass123"))
        self.assertTrue(authenticate_user("manager_bob", "coldchain2026"))

    def test_authenticate_user_failure(self):
        """Rejects incorrect password and unregistered username."""
        self.assertFalse(authenticate_user("operator_alice", "wrongpass"))
        self.assertFalse(authenticate_user("unknown_user", "securepass123"))
        self.assertFalse(authenticate_user("", ""))

    def test_create_and_decode_valid_token(self):
        """Token can be created and successfully decoded."""
        payload = {"sub": "operator_alice", "role": "operator"}
        token = create_access_token(payload)
        decoded = decode_access_token(token)
        self.assertEqual(decoded["sub"], "operator_alice")
        self.assertEqual(decoded["role"], "operator")
        self.assertIn("exp", decoded)
        self.assertIn("iat", decoded)

    def test_decode_tampered_token_fails(self):
        """Tampering with token payload or signature must raise ValueError."""
        payload = {"sub": "operator_alice"}
        # Sign with wrong secret key
        tampered_token = jwt.encode(payload, "wrong-secret-key-at-least-32-bytes!", algorithm=JWT_ALGORITHM)
        with self.assertRaises(ValueError) as ctx:
            decode_access_token(tampered_token)
        self.assertIn("Invalid token", str(ctx.exception))

    def test_decode_expired_token_fails(self):
        """Expired token must raise ValueError."""
        payload = {"sub": "operator_alice"}
        # Create token that expired 10 minutes ago
        expired_token = create_access_token(payload, expires_delta=timedelta(minutes=-10))
        with self.assertRaises(ValueError) as ctx:
            decode_access_token(expired_token)
        self.assertIn("Token has expired", str(ctx.exception))

    def test_require_auth_missing_header_raises_401(self):
        """Missing Authorization header raises HTTPException with status 401."""
        req = MagicMock()
        req.url.path = "/produce"
        req.method = "POST"
        req.headers = {}

        with self.assertRaises(HTTPException) as ctx:
            require_auth(req)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("Missing or invalid Authorization header", ctx.exception.detail)

    def test_require_auth_invalid_token_raises_401(self):
        """Invalid token string raises HTTPException with status 401."""
        req = MagicMock()
        req.url.path = "/produce"
        req.method = "POST"
        req.headers = {"Authorization": "Bearer invalid.fake.token"}

        with self.assertRaises(HTTPException) as ctx:
            require_auth(req)
        self.assertEqual(ctx.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
