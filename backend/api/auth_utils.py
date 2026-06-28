"""JWT token creation and verification utilities."""

import logging
import os
from datetime import UTC, datetime, timedelta

import jwt

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))


def _get_secret() -> str:
    """Get JWT secret from env or raise if not set."""
    if not JWT_SECRET:
        msg = (
            "JWT_SECRET env var not set. "
            "Generate: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
        raise RuntimeError(msg)
    return JWT_SECRET


def create_token(user_id: str, username: str, role: str) -> str:
    """Create a JWT token with user claims and expiration."""
    secret = _get_secret()
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Verify and decode a JWT token. Returns payload or None on failure."""
    secret = _get_secret()
    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": payload["sub"],
            "username": payload["username"],
            "role": payload["role"],
        }
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("JWT token invalid: %s", e)
        return None
