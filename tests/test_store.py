"""Tests for SQLite persistence layer (store.py)."""

import os
import tempfile

import pytest

from portalonline_gmap_scraper.api.store import (
    cancel_job,
    create_job,
    create_user,
    delete_user,
    get_audit_logs,
    get_db_stats,
    get_job,
    get_lead_stats,
    get_leads_by_job,
    get_next_queued,
    get_queue,
    get_queue_position,
    get_user_by_api_key,
    get_user_by_id,
    init_db,
    insert_leads_batch,
    list_jobs,
    list_users,
    log_audit,
    reindex_queue,
    run_cleanup,
    update_job_status,
    update_user,
)


@pytest.fixture
async def db():
    db_path = tempfile.mktemp(suffix=".db")
    conn = await init_db(db_path)
    yield conn
    await conn.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestUserCRUD:
    async def test_create_and_get_user(self, db):
        user = await create_user(db, "testuser", role="user")
        assert user["username"] == "testuser"
        assert user["role"] == "user"
        assert user["active"] is True

        fetched = await get_user_by_id(db, user["user_id"])
        assert fetched["username"] == "testuser"

    async def test_get_user_by_api_key(self, db):
        user = await create_user(db, "apiuser")
        fetched = await get_user_by_api_key(db, user["api_key"])
        assert fetched is not None
        assert fetched["user_id"] == user["user_id"]

    async def test_get_user_by_api_key_none(self, db):
        assert await get_user_by_api_key(db, "nonexistent") is None

    async def test_list_users(self, db):
        await create_user(db, "user1")
        await create_user(db, "user2")
        users = await list_users(db)
        assert len(users) == 2

    async def test_update_user(self, db):
        user = await create_user(db, "oldname")
        updated = await update_user(db, user["user_id"], username="newname")
        assert updated["username"] == "newname"

    async def test_delete_user(self, db):
        user = await create_user(db, "todelete")
        assert await delete_user(db, user["user_id"]) is True
        assert await get_user_by_id(db, user["user_id"]) is None

    async def test_delete_nonexistent_user(self, db):
        assert await delete_user(db, "nonexistent") is False


class TestJobCRUD:
    async def test_create_and_get_job(self, db):
        user = await create_user(db, "jobuser")
        job = await create_job(
            db, user["user_id"], "restoran", "Jakarta",
            "restoran in Jakarta",
        )
        assert job["status"] == "queued"
        fetched = await get_job(db, job["job_id"])
        assert fetched["keyword"] == "restoran"

    async def test_list_jobs_pagination(self, db):
        user = await create_user(db, "listuser")
        for i in range(5):
            await create_job(
                db, user["user_id"], f"kw{i}", "loc",
                f"kw{i} in loc",
            )
        result = await list_jobs(db, page=1, limit=3)
        assert len(result["jobs"]) == 3
        assert result["total"] == 5

    async def test_update_job_status(self, db):
        user = await create_user(db, "statususer")
        job = await create_job(db, user["user_id"], "kw", None, "kw")
        await update_job_status(db, job["job_id"], "running")
        updated = await get_job(db, job["job_id"])
        assert updated["status"] == "running"
        assert updated["started_at"] is not None

    async def test_cancel_job(self, db):
        user = await create_user(db, "canceluser")
        job = await create_job(db, user["user_id"], "kw", None, "kw")
        cancelled = await cancel_job(db, job["job_id"])
        assert cancelled["status"] == "cancelled"


class TestLeadOps:
    async def test_insert_and_get_leads(self, db):
        user = await create_user(db, "leaduser")
        job = await create_job(db, user["user_id"], "cafe", "Bandung", "cafe in Bandung")
        leads = [
            {
                "job_id": job["job_id"], "user_id": user["user_id"],
                "keyword": "cafe", "name": "Kopi Kenangan",
                "address": "Jl. Asia Afrika", "phone": "08123456789",
                "website": "kopikenangan.com", "rating": "4.5",
                "review_count": "120",
            }
        ]
        count = await insert_leads_batch(db, leads)
        assert count == 1

        results = await get_leads_by_job(db, job["job_id"])
        assert len(results) == 1

    async def test_dedup_leads(self, db):
        user = await create_user(db, "dedupuser")
        job = await create_job(db, user["user_id"], "kw", None, "kw")
        lead = {
            "job_id": job["job_id"], "user_id": user["user_id"],
            "keyword": "kw", "name": "Same Place",
            "address": "Same Address",
        }
        await insert_leads_batch(db, [lead])
        count = await insert_leads_batch(db, [lead])
        assert count == 0

    async def test_get_lead_stats(self, db):
        user = await create_user(db, "statsuser")
        job = await create_job(db, user["user_id"], "kw", None, "kw")
        await insert_leads_batch(db, [{
            "job_id": job["job_id"], "user_id": user["user_id"],
            "keyword": "kw", "name": "Place", "address": "Addr",
            "phone": "08123", "website": "site.com",
            "rating": "4.0", "review_count": "50",
        }])
        stats = await get_lead_stats(db, user["user_id"])
        assert stats["total_leads"] == 1
        assert stats["leads_with_phone"] == 1
        assert stats["leads_with_website"] == 1


class TestQueueOps:
    async def test_queue_position(self, db):
        user = await create_user(db, "queueuser")
        assert await get_queue_position(db) == 1

    async def test_get_queue(self, db):
        user = await create_user(db, "quser")
        await create_job(db, user["user_id"], "a", None, "a", queue_position=1)
        await create_job(db, user["user_id"], "b", None, "b", queue_position=2)
        q = await get_queue(db)
        assert len(q["queue"]) == 2

    async def test_get_next_queued(self, db):
        user = await create_user(db, "nquser")
        await create_job(db, user["user_id"], "first", None, "first", queue_position=1)
        await create_job(db, user["user_id"], "second", None, "second", queue_position=2)
        next_job = await get_next_queued(db)
        assert next_job["keyword"] == "first"

    async def test_reindex_queue(self, db):
        user = await create_user(db, "rixuser")
        await create_job(db, user["user_id"], "a", None, "a", queue_position=5)
        await create_job(db, user["user_id"], "b", None, "b", queue_position=10)
        await reindex_queue(db)
        next_job = await get_next_queued(db)
        assert next_job is not None


class TestAudit:
    async def test_log_and_get_audit(self, db):
        user = await create_user(db, "audituser")
        await log_audit(db, user["user_id"], "test.action", "target", "tid")
        logs = await get_audit_logs(db)
        assert logs["total"] >= 1


class TestCleanup:
    async def test_run_cleanup(self, db):
        result = await run_cleanup(db, older_than_days=9999)
        assert "deleted_jobs" in result
        assert "db_size_after_mb" in result


class TestDbStats:
    async def test_get_db_stats(self, db):
        stats = await get_db_stats(db)
        assert "row_counts" in stats
        assert "db_size_mb" in stats
