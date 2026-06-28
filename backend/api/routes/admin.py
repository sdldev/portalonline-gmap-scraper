"""Admin endpoints: audit logs, cleanup, DB stats."""

import logging

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from api.deps import get_db
from api.middleware.auth import require_admin
from api.models import (
    AuditLogPage,
    CleanupRequest,
    CleanupResponse,
    DbStatsResponse,
)
from api.store import get_audit_logs, get_dashboard_stats, get_db_stats, run_cleanup

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/audit-logs", response_model=AuditLogPage)
async def list_audit_logs(
    request: Request,
    user_id: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """GET /api/v1/admin/audit-logs (admin)."""
    return await get_audit_logs(
        db, user_id=user_id, action=action, target_type=target_type,
        from_date=from_date, to_date=to_date, page=page, limit=limit,
    )


@router.post("/cleanup", response_model=CleanupResponse)
async def trigger_cleanup(
    body: CleanupRequest,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """POST /api/v1/admin/cleanup (admin)."""
    return await run_cleanup(db, older_than_days=body.older_than_days)


@router.get("/db-stats", response_model=DbStatsResponse)
async def db_stats(
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """GET /api/v1/admin/db-stats (admin)."""
    return await get_db_stats(db)


class DashboardStatsResponse(BaseModel):
    total_users: int
    total_jobs: int
    total_leads: int
    active_jobs: int
    queued_jobs: int
    recent_jobs: list[dict]


@router.get("/stats", response_model=DashboardStatsResponse)
async def dashboard_stats(
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """GET /api/v1/admin/stats - Dashboard aggregate counts."""
    return await get_dashboard_stats(db)
