# Phase 1: Backend Auth + API

**Goal**: Add JWT authentication, dashboard stats endpoint, and user management helpers to the existing FastAPI backend.

**Dependencies**: None (pure backend, no frontend needed).

**Estimated Effort**: 2-3 days.

---

## Task 1.1: Add Dependencies

**File**: `pyproject.toml`

Add to `[project.dependencies]`:
```
"bcrypt>=4.1.0",
"PyJWT>=2.8.0",
```

Run: `uv sync`

**Verify**: `uv pip list | grep -iE "bcrypt|pyjwt"`

---

## Task 1.2: Database Migration - Add `password_hash` Column

**File**: `portalonline_gmap_scraper/api/store.py` (inside `init_db`)

Add after the existing `CREATE TABLE IF NOT EXISTS users` block:

```python
# Migration: add password_hash if missing
try:
    await db.execute(
        "ALTER TABLE users ADD COLUMN password_hash TEXT"
    )
    await db.commit()
except Exception:
    pass  # Column already exists

await db.execute(
    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
)
await db.commit()
```

**Verify**: Delete `data/portalonline.db`, start server, check schema with `sqlite3 data/portalonline.db ".schema users"`

---

## Task 1.3: Add Store Functions

**File**: `portalonline_gmap_scraper/api/store.py`

Add these functions:

```python
import bcrypt


async def get_user_by_username(
    db: aiosqlite.Connection, username: str
) -> dict[str, Any] | None:
    """Look up a user by username. Returns None if not found."""
    async with db.execute(
        "SELECT user_id, username, role, api_key, active, webhook_url, "
        "webhook_events, created_at FROM users WHERE username = ?",
        (username,),
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_user(row)


async def get_user_with_password(
    db: aiosqlite.Connection, username: str
) -> dict[str, Any] | None:
    """Look up user by username including password_hash for login."""
    async with db.execute(
        "SELECT user_id, username, password_hash, role, api_key, active "
        "FROM users WHERE username = ?",
        (username,),
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        return None
    return {
        "user_id": row[0],
        "username": row[1],
        "password_hash": row[2],
        "role": row[3],
        "api_key": row[4],
        "active": bool(row[5]),
    }


async def update_password_hash(
    db: aiosqlite.Connection,
    user_id: str,
    password_hash: str,
) -> None:
    """Update a user's password hash."""
    await db.execute(
        "UPDATE users SET password_hash = ? WHERE user_id = ?",
        (password_hash, user_id),
    )
    await db.commit()


async def update_api_key(
    db: aiosqlite.Connection,
    user_id: str,
    api_key: str,
) -> None:
    """Replace a user's API key."""
    await db.execute(
        "UPDATE users SET api_key = ? WHERE user_id = ?",
        (api_key, user_id),
    )
    await db.commit()
```

**Verify**: Import works, no syntax errors.

---

## Task 1.4: Add Pydantic Models

**File**: `portalonline_gmap_scraper/api/models.py`

Add these models:

```python
# --- Auth Models ---

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


class LogoutResponse(BaseModel):
    success: bool


# --- Dashboard Models ---

class RecentJob(BaseModel):
    job_id: str
    keyword: str
    location: str | None = None
    status: str
    leads_collected: int
    leads_total: int
    created_at: str


class DashboardStats(BaseModel):
    total_users: int
    total_jobs: int
    total_leads: int
    active_jobs: int
    queued_jobs: int
    recent_jobs: list[RecentJob]


# --- Password / API Key Generation Models ---

class PasswordGenerateResponse(BaseModel):
    password: str
    message: str


class ApiKeyGenerateResponse(BaseModel):
    api_key: str
    message: str
```

**Verify**: `python -c "from portalonline_gmap_scraper.api.models import LoginRequest, DashboardStats"`

---

## Task 1.5: Implement Auth Routes

**New file**: `portalonline_gmap_scraper/api/routes/auth.py`

```python
"""Authentication endpoints (login, logout)."""

import logging
import os
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request

from ..deps import get_db
from ..middleware.auth import require_user
from ..models import LoginRequest, LoginResponse, LogoutResponse, UserResponse
from ..store import get_user_with_password, log_audit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET", os.urandom(32).hex())
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def _create_token(user: dict) -> str:
    payload = {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "exp": datetime.now(UTC) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request, db=Depends(get_db)):
    """POST /api/v1/auth/login - Authenticate with username + password."""
    user = await get_user_with_password(db, body.username)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("password_hash"):
        raise HTTPException(
            status_code=401,
            detail="Password not set. Contact admin to generate a password.",
        )

    if not bcrypt.checkpw(
        body.password.encode("utf-8"),
        user["password_hash"].encode("utf-8"),
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user["active"]:
        raise HTTPException(status_code=403, detail="User account is inactive")

    token = _create_token(user)
    await log_audit(
        db, user["user_id"], "auth.login",
        ip_address=request.client.host if request.client else None,
    )

    return LoginResponse(
        token=token,
        user=UserResponse(
            user_id=user["user_id"],
            username=user["username"],
            role=user["role"],
            api_key=user["api_key"],
            active=user["active"],
            created_at="",
        ),
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    """POST /api/v1/auth/logout - Invalidate session (audit only)."""
    await log_audit(
        db, request.state.user_id, "auth.logout",
        ip_address=request.client.host if request.client else None,
    )
    return LogoutResponse(success=True)
```

**Verify**: Start server, test with curl after creating a user with password.

---

## Task 1.6: Implement Dashboard Stats Route

**New file**: `portalonline_gmap_scraper/api/routes/stats.py`

```python
"""Dashboard statistics endpoint."""

import logging

from fastapi import APIRouter, Depends, Request

from ..deps import get_db
from ..middleware.auth import require_admin
from ..models import DashboardStats, RecentJob

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """GET /api/v1/admin/stats - Aggregate counts + recent jobs."""
    async with db.execute("SELECT COUNT(*) FROM users") as cur:
        total_users = (await cur.fetchone())[0]
    async with db.execute("SELECT COUNT(*) FROM jobs") as cur:
        total_jobs = (await cur.fetchone())[0]
    async with db.execute("SELECT COUNT(*) FROM leads") as cur:
        total_leads = (await cur.fetchone())[0]
    async with db.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'running'"
    ) as cur:
        active_jobs = (await cur.fetchone())[0]
    async with db.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'queued'"
    ) as cur:
        queued_jobs = (await cur.fetchone())[0]

    async with db.execute(
        "SELECT j.job_id, j.keyword, j.location, j.status, "
        "j.leads_collected, j.leads_total, j.created_at "
        "FROM jobs j ORDER BY j.created_at DESC LIMIT 10"
    ) as cur:
        rows = await cur.fetchall()

    recent = [
        RecentJob(
            job_id=r[0], keyword=r[1], location=r[2], status=r[3],
            leads_collected=r[4], leads_total=r[5], created_at=r[6],
        )
        for r in rows
    ]

    return DashboardStats(
        total_users=total_users,
        total_jobs=total_jobs,
        total_leads=total_leads,
        active_jobs=active_jobs,
        queued_jobs=queued_jobs,
        recent_jobs=recent,
    )
```

**Verify**: `curl -H "X-API-Key: <admin_key>" http://localhost:8000/api/v1/admin/stats`

---

## Task 1.7: Implement User Management Routes (Generate Password / API Key)

**File**: `portalonline_gmap_scraper/api/routes/users.py`

Add two new endpoints to the existing users router:

```python
import bcrypt
import secrets
import string

from ..models import PasswordGenerateResponse, ApiKeyGenerateResponse
from ..store import update_password_hash, update_api_key


@router.post("/{user_id}/generate-password", response_model=PasswordGenerateResponse)
async def generate_password_route(
    user_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """POST /api/v1/users/{id}/generate-password (admin)."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(404, "User not found")

    chars = string.ascii_letters + string.digits + "!@#$%&*"
    password = "".join(secrets.choice(chars) for _ in range(16))
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    await update_password_hash(db, user_id, password_hash)
    await log_audit(
        db, request.state.user_id, "user.generate_password",
        target_type="user", target_id=user_id,
    )

    return PasswordGenerateResponse(
        password=password,
        message="Password updated. Save it now, it won't be shown again.",
    )


@router.post("/{user_id}/generate-api-key", response_model=ApiKeyGenerateResponse)
async def generate_api_key_route(
    user_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """POST /api/v1/users/{id}/generate-api-key (admin)."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(404, "User not found")

    new_key = f"pk_{secrets.token_hex(12)}"
    await update_api_key(db, user_id, new_key)
    await log_audit(
        db, request.state.user_id, "user.generate_api_key",
        target_type="user", target_id=user_id,
    )

    return ApiKeyGenerateResponse(
        api_key=new_key,
        message="API key regenerated. Old key is now invalid.",
    )
```

**Verify**: Create user, call generate-password, then login with the returned password.

---

## Task 1.8: Update Auth Middleware for JWT Support

**File**: `portalonline_gmap_scraper/api/middleware/auth.py`

Update `verify_api_key` to also try JWT:

```python
import jwt
from ..routes.auth import JWT_SECRET, JWT_ALGORITHM


async def verify_api_key(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Authenticate via JWT (Authorization: Bearer) or API key (X-API-Key)."""

    # 1. Try JWT first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user = await get_user_by_id(db, payload["user_id"])
            if user and user["active"]:
                request.state.user_id = user["user_id"]
                request.state.user_role = user["role"]
                request.state.username = user["username"]
                return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    # 2. Fallback to API key
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing authentication")

    user = await get_user_by_api_key(db, api_key)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not user["active"]:
        raise HTTPException(status_code=403, detail="User account is inactive")

    request.state.user_id = user["user_id"]
    request.state.user_role = user["role"]
    request.state.username = user["username"]
    return user
```

**Verify**: Both `Authorization: Bearer <jwt>` and `X-API-Key: <key>` work on any protected endpoint.

---

## Task 1.9: Register New Routes in App

**File**: `portalonline_gmap_scraper/api/app.py`

Add imports and include routers:

```python
from .routes.auth import router as auth_router
from .routes.stats import router as stats_router

# In create_app():
app.include_router(auth_router)
app.include_router(stats_router)
```

**Verify**: `curl http://localhost:8000/openapi.json | jq '.paths | keys'` shows new routes.

---

## Task 1.10: Write Tests

**New file**: `tests/test_auth.py`

```python
"""Tests for auth endpoints."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_login_success(client, admin_user):
    """Login returns JWT token with valid credentials."""
    resp = await client.post(
        f"/api/v1/users/{admin_user['user_id']}/generate-password",
        headers={"X-API-Key": admin_user["api_key"]},
    )
    password = resp.json()["password"]

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": password},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["username"] == "admin"


async def test_login_invalid_password(client, admin_user):
    """Login returns 401 with wrong password."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_login_unknown_user(client):
    """Login returns 401 for nonexistent user."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "nobody", "password": "test"},
    )
    assert resp.status_code == 401


async def test_logout(client, admin_user):
    """Logout returns success."""
    resp = await client.post(
        "/api/v1/auth/logout",
        headers={"X-API-Key": admin_user["api_key"]},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


async def test_dashboard_stats(client, admin_user):
    """Stats endpoint returns aggregate counts."""
    resp = await client.get(
        "/api/v1/admin/stats",
        headers={"X-API-Key": admin_user["api_key"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "total_jobs" in data
    assert "total_leads" in data


async def test_generate_password(client, admin_user):
    """Generate password returns a 16-char password."""
    resp = await client.post(
        f"/api/v1/users/{admin_user['user_id']}/generate-password",
        headers={"X-API-Key": admin_user["api_key"]},
    )
    assert resp.status_code == 200
    assert len(resp.json()["password"]) == 16


async def test_generate_api_key(client, admin_user):
    """Generate API key returns new key starting with pk_."""
    resp = await client.post(
        f"/api/v1/users/{admin_user['user_id']}/generate-api-key",
        headers={"X-API-Key": admin_user["api_key"]},
    )
    assert resp.status_code == 200
    assert resp.json()["api_key"].startswith("pk_")
```

**Run**: `.venv/bin/python -m pytest tests/test_auth.py -v`

---

## Verification Checklist

- [ ] `uv sync` installs bcrypt and PyJWT
- [ ] `users` table has `password_hash` column after server start
- [ ] `POST /api/v1/auth/login` returns JWT with valid credentials
- [ ] `POST /api/v1/auth/login` returns 401 with invalid credentials
- [ ] `POST /api/v1/auth/logout` returns success
- [ ] `GET /api/v1/admin/stats` returns user/job/lead counts
- [ ] `POST /api/v1/users/{id}/generate-password` returns 16-char password
- [ ] `POST /api/v1/users/{id}/generate-api-key` returns new `pk_` key
- [ ] JWT auth works on protected endpoints (`Authorization: Bearer <token>`)
- [ ] API key auth still works (backward compatible)
- [ ] All tests pass: `.venv/bin/python -m pytest tests/test_auth.py -v`
- [ ] Lint passes: `.venv/bin/python -m ruff check .`
