"""Health check and system monitoring endpoints."""

import logging
import time

import psutil
from fastapi import APIRouter, Depends, Request

from api.deps import get_db
from api.middleware.auth import require_user
from api.models import HealthResponse, SystemInfo
from api.store import get_db_stats

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

_start_time = time.time()


@router.get("/api/v1/health", response_model=HealthResponse)
async def health_check(db=Depends(get_db)):
    """GET /api/v1/health - DB ping, 200 or 503."""
    try:
        await db.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        version="0.1.0",
        db_connected=db_ok,
        uptime_seconds=round(time.time() - _start_time, 1),
    )


@router.get("/api/v1/system", response_model=SystemInfo)
async def system_info(
    request: Request,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    """GET /api/v1/system - RAM, CPU, disk, jobs."""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(".")
    cpu = psutil.cpu_percent(interval=0.1)

    cursor = await db.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'running'"
    )
    active_jobs = (await cursor.fetchone())[0]

    cursor2 = await db.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'queued'"
    )
    queued_jobs = (await cursor2.fetchone())[0]

    stats = await get_db_stats(db)

    return SystemInfo(
        ram_used_mb=round(mem.used / (1024 * 1024), 1),
        ram_total_mb=round(mem.total / (1024 * 1024), 1),
        ram_percent=round(mem.percent, 1),
        cpu_percent=round(cpu, 1),
        disk_used_gb=round(disk.used / (1024**3), 2),
        disk_total_gb=round(disk.total / (1024**3), 2),
        disk_percent=round(disk.percent, 1),
        active_jobs=active_jobs,
        queued_jobs=queued_jobs,
        uptime_seconds=round(time.time() - _start_time, 1),
        db_size_mb=stats["db_size_mb"],
    )
