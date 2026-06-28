"""Tests for JWT auth, login, logout, dashboard stats, and user helpers."""

import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from backend.api.app import create_app
from backend.api.job_manager import JobManager
from backend.api.store import init_db


@pytest.fixture
async def client():
    """Create test app with in-memory DB, admin user (API key + password)."""
    db_path = tempfile.mktemp(suffix=".db")
    db = await init_db(db_path)

    from backend.api import store as store_mod
    old_path = store_mod.DB_PATH
    store_mod.DB_PATH = db_path

    os.environ["ADMIN_API_KEY"] = "test-admin-key"
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-tests-only"

    app = create_app()
    app.state.db = db
    app.state.job_manager = JobManager(db)

    # Create admin user with password
    from backend.api.store import create_user_with_password
    _ = await create_user_with_password(
        db, "admin", password="admin123", role="admin",
        api_key="test-admin-key",
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    await db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)
    store_mod.DB_PATH = old_path


class TestJWTUtils:
    """Unit tests for JWT token creation and verification."""

    def test_create_and_verify_token(self):
        from backend.api.auth_utils import create_token, verify_token

        os.environ["JWT_SECRET"] = "test-secret"
        token = create_token("user1", "testuser", "user")
        assert isinstance(token, str)

        payload = verify_token(token)
        assert payload is not None
        assert payload["user_id"] == "user1"
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"

    def test_verify_invalid_token(self):
        from backend.api.auth_utils import verify_token

        os.environ["JWT_SECRET"] = "test-secret"
        payload = verify_token("invalid.token.here")
        assert payload is None

    def test_raises_without_secret(self):
        import importlib

        import backend.api.auth_utils as mod

        old_secret = os.environ.pop("JWT_SECRET", None)
        importlib.reload(mod)

        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            mod.create_token("x", "y", "z")

        if old_secret:
            os.environ["JWT_SECRET"] = old_secret
        importlib.reload(mod)


class TestAuthEndpoints:
    """Integration tests for login and logout endpoints."""

    async def test_login_success(self, client):
        """POST /api/v1/auth/login returns JWT with valid credentials."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["token"]) > 0
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    async def test_login_invalid_credentials(self, client):
        """POST /api/v1/auth/login returns 401 with bad password."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        """POST /api/v1/auth/login returns 401 for unknown user."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "whatever"},
        )
        assert resp.status_code == 401

    async def test_logout_success(self, client):
        """POST /api/v1/auth/logout returns success with valid JWT."""
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        token = login_resp.json()["token"]

        resp = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_logout_without_token(self, client):
        """POST /api/v1/auth/logout returns 401 without auth."""
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 401


class TestDashboardStats:
    """Tests for admin dashboard stats endpoint."""

    async def test_dashboard_stats(self, client):
        """GET /api/v1/admin/stats returns aggregate counts."""
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "total_jobs" in data
        assert "total_leads" in data
        assert "active_jobs" in data
        assert "queued_jobs" in data
        assert isinstance(data["recent_jobs"], list)
        assert data["total_users"] >= 1

    async def test_dashboard_stats_requires_admin(self, client):
        """Non-admin cannot access dashboard stats."""
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"X-API-Key": "invalid-key"},
        )
        assert resp.status_code == 401


class TestGeneratePassword:
    """Tests for generate-password endpoint."""

    async def test_generate_password(self, client):
        """POST /api/v1/users/{id}/generate-password returns 16-char password."""
        # Get admin user ID
        resp = await client.get(
            "/api/v1/users",
            headers={"X-API-Key": "test-admin-key"},
        )
        users = resp.json()
        admin = next(u for u in users if u["username"] == "admin")
        user_id = admin["user_id"]

        resp = await client.post(
            f"/api/v1/users/{user_id}/generate-password",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["password"]) == 16

    async def test_generate_password_nonexistent_user(self, client):
        """Returns 404 for unknown user."""
        resp = await client.post(
            "/api/v1/users/nonexistent/generate-password",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert resp.status_code == 404


class TestGenerateApiKey:
    """Tests for generate-api-key endpoint."""

    async def test_generate_api_key(self, client):
        """POST /api/v1/users/{id}/generate-api-key returns new pk_ key."""
        resp = await client.get(
            "/api/v1/users",
            headers={"X-API-Key": "test-admin-key"},
        )
        users = resp.json()
        admin = next(u for u in users if u["username"] == "admin")
        user_id = admin["user_id"]

        resp = await client.post(
            f"/api/v1/users/{user_id}/generate-api-key",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["api_key"].startswith("pk_")

    async def test_generate_api_key_nonexistent_user(self, client):
        """Returns 404 for unknown user."""
        resp = await client.post(
            "/api/v1/users/nonexistent/generate-api-key",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert resp.status_code == 404
