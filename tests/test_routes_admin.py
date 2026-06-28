"""Tests for admin endpoints."""

import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from portalonline_gmap_scraper.api.app import create_app
from portalonline_gmap_scraper.api.job_manager import JobManager
from portalonline_gmap_scraper.api.store import init_db


@pytest.fixture
async def client():
    db_path = tempfile.mktemp(suffix=".db")
    db = await init_db(db_path)

    from portalonline_gmap_scraper.api import store
    old_path = store.DB_PATH
    store.DB_PATH = db_path

    os.environ["ADMIN_API_KEY"] = "test-admin-key"

    app = create_app()
    app.state.db = db
    app.state.job_manager = JobManager(db)

    from portalonline_gmap_scraper.api.middleware.auth import ensure_default_admin
    await ensure_default_admin(db)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    await db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)
    store.DB_PATH = old_path


class TestAdminRoutes:
    async def test_audit_logs(self, client):
        resp = await client.get(
            "/api/v1/admin/audit-logs",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert resp.status_code == 200

    async def test_db_stats(self, client):
        resp = await client.get(
            "/api/v1/admin/db-stats",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "row_counts" in data

    async def test_cleanup(self, client):
        resp = await client.post(
            "/api/v1/admin/cleanup",
            json={"older_than_days": 30},
            headers={"X-API-Key": "test-admin-key"},
        )
        assert resp.status_code == 200

    async def test_admin_requires_admin_key(self, client):
        resp = await client.get(
            "/api/v1/admin/audit-logs",
            headers={"X-API-Key": "invalid-key"},
        )
        assert resp.status_code == 401
