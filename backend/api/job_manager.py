"""Job Manager: queue orchestration, scraper integration, timeout, graceful shutdown."""

import asyncio
import logging
import os
from typing import Any

import aiosqlite

from api.store import (
    cancel_job,
    create_job,
    get_next_queued,
    get_queue_position,
    insert_leads_batch,
    log_audit,
    reindex_queue,
    update_job_status,
)
from scraper import scrape, scrape_smart

logger = logging.getLogger(__name__)


class JobManager:
    """Manages job lifecycle: submit, queue, run, cancel, timeout."""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self._active_job_id: str | None = None
        self._active_task: asyncio.Task | None = None
        self._cancel_event: asyncio.Event = asyncio.Event()
        self._running = True
        self._progress: dict[str, dict[str, Any]] = {}

    # --- Public API ---

    async def submit(self, user_id: str, job_data: dict[str, Any]) -> dict[str, Any]:
        """Validate, check duplicate, create job, start or enqueue."""
        keyword = job_data["keyword"]
        location = job_data.get("location")
        target = job_data.get("target", 25)
        smart = job_data.get("smart", True)
        query = f"{keyword} in {location}" if location else keyword

        await self._check_disk_space()

        existing = await self._check_duplicate(user_id, keyword, location)
        if existing:
            return {"_duplicate": True, "existing_job_id": existing["job_id"]}

        has_active = self._active_job_id is not None
        queue_pos = await get_queue_position(self.db) if has_active else None

        job = await create_job(
            self.db,
            user_id,
            keyword,
            location,
            query,
            target=target,
            smart=smart,
            queue_position=queue_pos,
        )

        await log_audit(self.db, user_id, "job.create", "job", job["job_id"])

        if not has_active:
            await self._start_job(job)
        else:
            logger.info("Job %s enqueued at position %d", job["job_id"], queue_pos)

        return job

    async def cancel(self, job_id: str) -> dict[str, Any]:
        """Cancel job. RBAC checking done at route level."""
        if self._active_job_id == job_id:
            self._cancel_event.set()
        await cancel_job(self.db, job_id)
        await reindex_queue(self.db)
        return await self.db.execute_fetchall(
            "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
        )

    def get_progress(self, job_id: str) -> dict[str, Any] | None:
        """Return in-memory progress dict for a job, or None if not tracked."""
        return self._progress.get(job_id)

    # --- Internal ---

    async def _start_job(self, job: dict[str, Any]) -> None:
        self._active_job_id = job["job_id"]
        self._cancel_event.clear()
        await update_job_status(self.db, job["job_id"], "running")
        await log_audit(self.db, job["user_id"], "job.start", "job", job["job_id"])

        timeout = int(os.getenv("MAX_JOB_DURATION_MINUTES", "30")) * 60

        self._active_task = asyncio.create_task(
            self._run_job_with_timeout(job, timeout)
        )

    async def _run_job_with_timeout(self, job: dict[str, Any], timeout: int) -> None:
        try:
            await asyncio.wait_for(self._run_job(job), timeout=timeout)
        except TimeoutError:
            logger.warning("Job %s timed out after %ds", job["job_id"], timeout)
            await update_job_status(
                self.db,
                job["job_id"],
                "failed",
                error=f"Job timed out after {timeout}s",
            )
            await log_audit(
                self.db, job["user_id"], "job.timeout", "job", job["job_id"]
            )
        except asyncio.CancelledError:
            await update_job_status(
                self.db,
                job["job_id"],
                "cancelled",
                error="Job cancelled",
            )
        except Exception as e:
            logger.exception("Job %s failed", job["job_id"])
            await update_job_status(
                self.db,
                job["job_id"],
                "failed",
                error=f"Job failed: {type(e).__name__}",
            )
        finally:
            await self._dequeue_next()

    async def _run_job(self, job: dict[str, Any]) -> None:
        """Execute scraper and persist results."""
        if job["smart"]:
            results = await scrape_smart(
                query=job["query"],
                max_tabs=1,
            )
        else:
            results = await scrape(
                query=job["query"],
                target=job["target"],
                max_tabs=1,
            )

        leads = [
            {
                "job_id": job["job_id"],
                "user_id": job["user_id"],
                "keyword": job["keyword"],
                "name": r.get("name", ""),
                "address": r.get("address", ""),
                "phone": r.get("phone", "N/A"),
                "website": r.get("website", "N/A"),
                "rating": str(r.get("rating", "N/A")),
                "review_count": str(r.get("review_count", "N/A")),
            }
            for r in results
        ]

        inserted = await insert_leads_batch(self.db, leads)
        await update_job_status(
            self.db,
            job["job_id"],
            "completed",
            leads_collected=inserted,
            leads_total=len(results),
        )
        await log_audit(self.db, job["user_id"], "job.complete", "job", job["job_id"])

    async def _dequeue_next(self) -> None:
        """Start next queued job if any, otherwise mark idle."""
        self._active_job_id = None
        self._active_task = None

        next_job = await get_next_queued(self.db)
        if next_job:
            await self._start_job(next_job)
            await reindex_queue(self.db)
        else:
            logger.debug("Queue empty, worker idle")

    async def _check_duplicate(
        self, user_id: str, keyword: str, location: str | None
    ) -> dict[str, Any] | None:
        loc = location or ""
        cursor = await self.db.execute(
            "SELECT job_id FROM jobs WHERE user_id = ? AND keyword = ? "
            "AND COALESCE(location, '') = ? AND status IN ('queued', 'running') "
            "LIMIT 1",
            (user_id, keyword, loc),
        )
        row = await cursor.fetchone()
        if row:
            return {"job_id": row[0]}
        return None

    async def _check_disk_space(self) -> None:
        limit = int(os.getenv("DISK_USAGE_LIMIT_PERCENT", "90"))
        try:
            stat = os.statvfs("data")
            usage = (1 - stat.f_bavail / stat.f_blocks) * 100
            if usage > limit:
                raise RuntimeError(f"Disk usage {usage:.1f}% exceeds limit {limit}%")
        except FileNotFoundError:
            pass

    async def shutdown(self) -> None:
        """Graceful shutdown: cancel active job, close DB."""
        self._running = False
        if self._active_task:
            self._cancel_event.set()
            self._active_task.cancel()
            try:
                await self._active_task
            except asyncio.CancelledError:
                pass
        if self._active_job_id:
            await update_job_status(
                self.db,
                self._active_job_id,
                "failed",
                error="Server shutting down",
            )
