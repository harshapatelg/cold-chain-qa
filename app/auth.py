"""
Authentication module using PyJWT for Cold-Chain Service.

Handles JWT token creation, signature verification, and FastAPI dependency
injection for route security. Includes two pre-configured demo users for
lab evaluation and automated tests.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_EXPIRATION_SECONDS,
    DEMO_USERS,
    is_defect_active,
)

security_scheme = HTTPBearer(auto_error=False)


def authenticate_user(username: str, password: str) -> bool:
    """Verifies username and password against hardcoded demo users."""
    if username in DEMO_USERS and DEMO_USERS[username] == password:
        return True
    return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT with expiration timestamp."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(seconds=JWT_EXPIRATION_SECONDS)
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates JWT token signature and expiration.
    Raises ValueError on token tampering, invalid signature, or expiration.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")


def require_auth(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency enforcing HTTP Bearer JWT authentication.
    
    Seeded Defect 3 (Missing 401 check):
    When active, requests to GET /alerts bypass token validation and return
    a dummy operator context, allowing unauthorized access.
    """
    path = request.url.path
    if is_defect_active(3) and path == "/alerts" and request.method == "GET":
        # SEEDED DEFECT #3: Bypass 401 check on GET /alerts
        return {"sub": "unauthenticated_guest", "role": "bypass"}

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
