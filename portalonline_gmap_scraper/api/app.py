"""FastAPI application factory and lifespan management."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .cleanup import CleanupScheduler
from .job_manager import JobManager
from .middleware.auth import ensure_default_admin
from .routes import (
    admin as admin_routes,
)
from .routes import (
    config,
    health,
    jobs,
    queue,
    results,
    sse,
    users,
)
from .store import init_db

logger = logging.getLogger(__name__)

_job_manager: JobManager | None = None
_cleanup_scheduler: CleanupScheduler | None = None


def get_job_manager() -> JobManager:
    if _job_manager is None:
        raise RuntimeError("JobManager not initialized")
    return _job_manager



@asynccontextmanager
async def lifespan(app: FastAPI):
    global _job_manager, _cleanup_scheduler

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    db = await init_db()
    app.state.db = db
    logger.info("Database initialized")

    admin_key = await ensure_default_admin(db)
    if admin_key:
        logger.info("Admin API key: %s", admin_key)

    await _recover_orphan_jobs(db)

    _job_manager = JobManager(db)
    app.state.job_manager = _job_manager

    _cleanup_scheduler = CleanupScheduler(db)
    await _cleanup_scheduler.start()

    yield

    if _job_manager:
        await _job_manager.shutdown()
    if _cleanup_scheduler:
        await _cleanup_scheduler.stop()
    await db.close()
    logger.info("Server shut down")


async def _recover_orphan_jobs(db) -> None:
    await db.execute(
        "UPDATE jobs SET status = 'failed', error = 'Server restarted', "
        "completed_at = datetime('now') WHERE status = 'running'"
    )
    await db.commit()

    cursor2 = await db.execute(
        "SELECT job_id FROM jobs WHERE status = 'queued' "
        "ORDER BY queue_position ASC"
    )
    job_ids = [row[0] for row in await cursor2.fetchall()]
    for idx, job_id in enumerate(job_ids, start=1):
        await db.execute(
            "UPDATE jobs SET queue_position = ? WHERE job_id = ?",
            (idx, job_id),
        )
    await db.commit()
    if job_ids:
        logger.info("Recovered %d queued jobs after restart", len(job_ids))




def create_app() -> FastAPI:
    app = FastAPI(
        title="PortalOnline GMap Scraper API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    cors_origins = os.getenv("CORS_ORIGINS", "*")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(users.router)
    app.include_router(jobs.router)
    app.include_router(health.router)
    app.include_router(results.router)
    app.include_router(queue.router)
    app.include_router(admin_routes.router)
    app.include_router(sse.router)
    app.include_router(config.router)

    return app
