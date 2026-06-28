"""API Key authentication and RBAC middleware."""

import logging
import os
from typing import Any

import aiosqlite
from fastapi import Depends, HTTPException, Request

from ..store import create_user, get_user_by_api_key

logger = logging.getLogger(__name__)


async def get_db(request: Request) -> aiosqlite.Connection:
    return request.app.state.db


async def verify_api_key(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Extract X-API-Key header, look up user, attach to request state."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    user = await get_user_by_api_key(db, api_key)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not user["active"]:
        raise HTTPException(status_code=403, detail="User account is inactive")

    request.state.user_id = user["user_id"]
    request.state.user_role = user["role"]
    request.state.username = user["username"]
    return user


async def require_admin(
    request: Request,
    user: dict[str, Any] = Depends(verify_api_key),
) -> dict[str, Any]:
    """Require admin role."""
    if request.state.user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def require_user(
    request: Request,
    user: dict[str, Any] = Depends(verify_api_key),
) -> dict[str, Any]:
    """Require authenticated user (any role)."""
    return user


async def get_optional_user(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any] | None:
    """Try to authenticate, but don't fail if missing."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    user = await get_user_by_api_key(db, api_key)
    if user is None or not user["active"]:
        return None
    request.state.user_id = user["user_id"]
    request.state.user_role = user["role"]
    return user


async def ensure_default_admin(db: aiosqlite.Connection) -> str:
    """Create default admin user if no users exist."""
    existing = await db.execute_fetchall("SELECT COUNT(*) FROM users")
    if existing and existing[0][0] > 0:
        return ""

    admin_key = os.getenv("ADMIN_API_KEY", "")
    if not admin_key:
        admin_key = f"admin_{os.urandom(16).hex()}"
        logger.warning(
            "ADMIN_API_KEY not set. Generated admin key: %s", admin_key
        )

    admin = await create_user(db, "admin", role="admin", api_key=admin_key)
    logger.info("Default admin user created: %s", admin["user_id"])
    return admin_key
