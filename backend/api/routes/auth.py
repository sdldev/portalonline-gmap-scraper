"""Authentication endpoints: login (JWT), logout."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth_utils import create_token
from api.deps import get_db
from api.middleware.auth import verify_jwt_token
from api.store import verify_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    success: bool = True
    token: str
    user_id: str
    username: str
    role: str


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db=Depends(get_db),
):
    """POST /api/v1/auth/login - Username + password -> JWT token."""
    user = await verify_password(db, body.username, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user["user_id"], user["username"], user["role"])
    return {
        "success": True,
        "token": token,
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
    }


@router.post("/logout")
async def logout(
    request: Request,
    user: dict = Depends(verify_jwt_token),
):
    """POST /api/v1/auth/logout - Client-side token discard."""
    return {"success": True, "message": "Logged out successfully"}
