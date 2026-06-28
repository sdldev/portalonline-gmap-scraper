"""User management endpoints (admin CRUD)."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from ..deps import get_db
from ..middleware.auth import require_admin, require_user
from ..models import UserCreate, UserResponse, UserUpdate
from ..store import (
    create_user,
    delete_user,
    generate_random_password,
    get_user_by_id,
    list_users,
    regenerate_api_key,
    update_user,
    update_user_password,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("", response_model=UserResponse)
async def create_user_route(
    body: UserCreate,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """POST /api/v1/users - Create user (admin)."""
    user = await create_user(db, body.username, role=body.role)
    return user


@router.get("", response_model=list[UserResponse])
async def list_users_route(
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """GET /api/v1/users - List users (admin)."""
    return await list_users(db)


@router.get("/me", response_model=UserResponse)
async def get_me(
    request: Request,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    """GET /api/v1/users/me - Own profile."""
    result = await get_user_by_id(db, request.state.user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_route(
    user_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """GET /api/v1/users/{id} - User detail (admin)."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_route(
    user_id: str,
    body: UserUpdate,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """PATCH /api/v1/users/{id} - Update user (admin)."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    updated = await update_user(
        db, user_id,
        username=body.username,
        role=body.role,
        active=body.active,
        webhook_url=body.webhook_url,
        webhook_events=json.dumps(body.webhook_events) if body.webhook_events else None,
    )
    return updated


@router.delete("/{user_id}")
async def delete_user_route(
    user_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """DELETE /api/v1/users/{id} - Delete user (admin)."""
    deleted = await delete_user(db, user_id)
    if not deleted:
        raise HTTPException(404, "User not found")
    return {"success": True}


@router.post("/{user_id}/generate-password")
async def generate_password_route(
    user_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """POST /api/v1/users/{id}/generate-password - Generate 16-char password."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(404, "User not found")

    password = generate_random_password()
    await update_user_password(db, user_id, password)

    await log_audit_generate(db, user_id, request, "password")
    return {"success": True, "password": password}


@router.post("/{user_id}/generate-api-key")
async def generate_api_key_route(
    user_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """POST /api/v1/users/{id}/generate-api-key - Regenerate API key."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(404, "User not found")

    new_key = await regenerate_api_key(db, user_id)
    if new_key is None:
        raise HTTPException(404, "User not found")

    await log_audit_generate(db, user_id, request, "api_key")
    return {"success": True, "api_key": new_key}


async def log_audit_generate(db, user_id: str, request: Request, key_type: str):
    """Log audit entry for key generation."""
    from ..store import log_audit

    ip = request.client.host if request.client else None
    await log_audit(
        db,
        user_id=request.state.user_id,
        action=f"generate_{key_type}",
        target_type="user",
        target_id=user_id,
        details=f"Generated new {key_type}",
        ip_address=ip,
    )
