"""Tests for results query engine."""

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


class TestResultsRoutes:
    async def test_list_results(self, client):
        resp = await client.get(
            "/api/v1/results",
            headers={"X-API-Key": "test-admin-key"},
        )
        assert resp.status_code in (200, 400)

    async def test_results_unauthorized(self, client):
        resp = await client.get("/api/v1/results")
        assert resp.status_code == 401
