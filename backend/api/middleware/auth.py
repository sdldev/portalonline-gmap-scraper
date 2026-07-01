"""API Key authentication and RBAC middleware."""

import logging
import os
from typing import Any

import aiosqlite
from fastapi import Depends, HTTPException, Request

from api.store import create_user, get_user_by_api_key

logger = logging.getLogger(__name__)


async def get_db(request: Request) -> aiosqlite.Connection:
    """Dependency returning the aiosqlite connection from app state."""
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
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Require admin role. Tries JWT Bearer token first, falls back to X-API-Key."""
    from api.auth_utils import verify_token
    from api.store import get_user_by_id

    auth_header = request.headers.get("Authorization", "")
    api_key = request.headers.get("X-API-Key")

    user = None

    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        payload = verify_token(token)
        if payload:
            user = await get_user_by_id(db, payload["user_id"])
    elif api_key:
        user = await get_user_by_api_key(db, api_key)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication")
    if not user["active"]:
        raise HTTPException(status_code=403, detail="User account is inactive")
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    request.state.user_id = user["user_id"]
    request.state.user_role = user["role"]
    request.state.username = user["username"]
    return user


async def require_user(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Require authenticated user (any role). Tries JWT first, then API key."""
    from api.auth_utils import verify_token
    from api.store import get_user_by_id

    auth_header = request.headers.get("Authorization", "")
    api_key = request.headers.get("X-API-Key")

    user = None

    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        payload = verify_token(token)
        if payload:
            user = await get_user_by_id(db, payload["user_id"])
    elif api_key:
        user = await get_user_by_api_key(db, api_key)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication")
    if not user["active"]:
        raise HTTPException(status_code=403, detail="User account is inactive")

    request.state.user_id = user["user_id"]
    request.state.user_role = user["role"]
    request.state.username = user["username"]
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
        logger.warning("ADMIN_API_KEY not set. Generated admin key: %s...%s", admin_key[:12], admin_key[-4:])

    admin = await create_user(db, "admin", role="admin", api_key=admin_key)
    logger.info("Default admin user created: %s", admin["user_id"])
    return admin_key


async def verify_jwt_token(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Extract Authorization: Bearer <token>, verify JWT, attach to request state."""
    from api.auth_utils import verify_token
    from api.store import get_user_by_id

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication")

    token = auth_header.removeprefix("Bearer ")
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await get_user_by_id(db, payload["user_id"])
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    if not user["active"]:
        raise HTTPException(status_code=403, detail="User account is inactive")

    request.state.user_id = user["user_id"]
    request.state.user_role = user["role"]
    request.state.username = user["username"]
    return user


async def require_jwt_admin(
    request: Request,
    user: dict[str, Any] = Depends(verify_jwt_token),
) -> dict[str, Any]:
    """Require JWT auth + admin role."""
    if request.state.user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def optional_jwt_token(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any] | None:
    """Try to authenticate via JWT, but don't fail if missing/invalid."""
    from api.auth_utils import verify_token
    from api.store import get_user_by_id

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.removeprefix("Bearer ")
    payload = verify_token(token)
    if payload is None:
        return None

    user = await get_user_by_id(db, payload["user_id"])
    if user is None or not user["active"]:
        return None

    request.state.user_id = user["user_id"]
    request.state.user_role = user["role"]
    request.state.username = user["username"]
    return user
