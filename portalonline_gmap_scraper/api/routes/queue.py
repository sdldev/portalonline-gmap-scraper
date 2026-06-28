"""Queue management endpoints (admin + user views)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from ..deps import get_db
from ..middleware.auth import require_admin, require_user
from ..models import QueueStatus
from ..store import get_job, get_queue, reindex_queue, update_job_status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/queue", tags=["queue"])


class ReorderBody:
    def __init__(self, position: int):
        self.position = position


@router.get("", response_model=QueueStatus)
async def view_queue(
    request: Request,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    is_admin = request.state.user_role == "admin"
    uid = None if is_admin else request.state.user_id
    return await get_queue(db, user_id=uid)


@router.patch("/{job_id}")
async def reorder_queue_item(
    job_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    body = await request.json()
    position = body.get("position")
    if position is None or not isinstance(position, int) or position < 1:
        raise HTTPException(400, "Invalid position")

    await db.execute(
        "UPDATE jobs SET queue_position = ? WHERE job_id = ?",
        (position, job_id),
    )
    await db.commit()
    await reindex_queue(db)
    return {"success": True}


@router.delete("/{job_id}")
async def remove_from_queue(
    job_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    job = await get_job(db, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    await update_job_status(db, job_id, "cancelled")
    await reindex_queue(db)
    return {"success": True}
