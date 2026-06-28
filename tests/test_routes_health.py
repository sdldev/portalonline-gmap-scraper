"""Tests for health and system endpoints."""

import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from backend.api.app import create_app
from backend.api.job_manager import JobManager
from backend.api.store import init_db


@pytest.fixture
async def client():
    db_path = tempfile.mktemp(suffix=".db")
    db = await init_db(db_path)

    from backend.api import store
    old_path = store.DB_PATH
    store.DB_PATH = db_path

    os.environ["ADMIN_API_KEY"] = "test-admin-key"

    app = create_app()
    app.state.db = db
    app.state.job_manager = JobManager(db)

    from backend.api.middleware.auth import ensure_default_admin
    await ensure_default_admin(db)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    await db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)
    store.DB_PATH = old_path


class TestHealthRoutes:
    async def test_health_check(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    async def test_system_endpoint(self, client):
        resp = await client.get(
            "/api/v1/system",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "ram_used_mb" in data
