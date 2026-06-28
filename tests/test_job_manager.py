"""Tests for JobManager queue orchestration."""

import os
import tempfile

import pytest

from portalonline_gmap_scraper.api.job_manager import JobManager
from portalonline_gmap_scraper.api.store import (
    create_user,
    get_job,
    init_db,
)


@pytest.fixture
async def db():
    db_path = tempfile.mktemp(suffix=".db")
    conn = await init_db(db_path)
    yield conn
    await conn.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
async def manager(db):
    return JobManager(db)


class TestJobManagerSubmit:
    async def test_submit_creates_job(self, db, manager):
        user = await create_user(db, "testuser")
        result = await manager.submit(user["user_id"], {
            "keyword": "restoran", "location": "Jakarta", "target": 10,
        })
        assert "job_id" in result
        assert result["status"] in ("queued", "running")

    async def test_duplicate_detection(self, db, manager):
        user = await create_user(db, "dupuser")
        await manager.submit(user["user_id"], {
            "keyword": "same", "location": "same",
        })
        result = await manager.submit(user["user_id"], {
            "keyword": "same", "location": "same",
        })
        assert "error" in result

    async def test_cancel_job(self, db, manager):
        user = await create_user(db, "canceluser")
        job = await manager.submit(user["user_id"], {
            "keyword": "tocancel", "location": "loc",
        })
        if "error" not in job:
            await manager.cancel(job["job_id"])
            updated = await get_job(db, job["job_id"])
            assert updated["status"] == "cancelled"

    async def test_get_progress_none(self, manager):
        assert manager.get_progress("nonexistent") is None
