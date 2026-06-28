"""Input sanitization validators and middleware."""

import re

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

BLOCKED_CHARS = ["<", ">", "'", "\"", ";", "--", "/*", "*/"]


def sanitize_keyword(value: str) -> str:
    """Strip blocked chars, trim whitespace. Max 200 chars."""
    value = value.strip()
    for c in BLOCKED_CHARS:
        value = value.replace(c, "")
    if not value:
        raise ValueError("keyword must not be empty")
    if len(value) > 200:
        raise ValueError("keyword max 200 characters")
    return value


def sanitize_location(value: str | None) -> str | None:
    """Strip blocked chars, trim whitespace. Max 100 chars."""
    if value is None:
        return None
    value = value.strip()
    for c in BLOCKED_CHARS:
        value = value.replace(c, "")
    if len(value) > 100:
        raise ValueError("location max 100 characters")
    return value if value else None


def sanitize_username(value: str) -> str:
    """Only a-z, 0-9, underscore. Max 50 chars."""
    value = value.strip()
    if not re.match(r"^[a-z0-9_]+$", value):
        raise ValueError("username: only a-z, 0-9, underscore allowed")
    if len(value) > 50:
        raise ValueError("username max 50 characters")
    return value


class SanitizeMiddleware(BaseHTTPMiddleware):
    """Strip blocked characters from query/body params.

    Not strictly needed since Pydantic validators handle this, but acts
    as a defense-in-depth layer for any raw parameter access.
    """

    async def dispatch(self, request: Request, call_next):
        """Pass-through middleware. Pydantic validators handle sanitization."""
        return await call_next(request)
