"""Jobs endpoints for PortalOnline GMap Scraper API."""

import csv
import io
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from ..deps import get_db, get_job_manager
from ..middleware.auth import require_user
from ..models import (
    JobCreate,
    JobResponse,
    JobsPage,
)
from ..store import get_job, get_leads_by_job, list_jobs

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse)
async def create_job_route(
    body: JobCreate,
    request: Request,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    manager = get_job_manager(request)
    result = await manager.submit(request.state.user_id, body.model_dump())
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=409,
            detail={
                "code": result["error"],
                "message": "Duplicate job exists",
                "existing_job_id": result.get("existing_job_id"),
            },
        )
    return result


@router.get("", response_model=JobsPage)
async def list_jobs_route(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    user_id: str | None = None,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    is_admin = request.state.user_role == "admin"
    filter_uid = user_id if is_admin and user_id else (
        None if is_admin else request.state.user_id
    )
    return await list_jobs(db, user_id=filter_uid, status=status,
                           keyword=keyword, page=page, limit=limit)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_route(
    job_id: str,
    request: Request,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    job = await get_job(db, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    is_admin = request.state.user_role == "admin"
    if not is_admin and job["user_id"] != request.state.user_id:
        raise HTTPException(403, "Access denied")
    return job


@router.delete("/{job_id}")
async def cancel_job_route(
    job_id: str,
    request: Request,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    job = await get_job(db, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    is_admin = request.state.user_role == "admin"
    if not is_admin and job["user_id"] != request.state.user_id:
        raise HTTPException(403, "Access denied")
    manager = get_job_manager(request)
    await manager.cancel(job_id)
    return {"success": True, "job_id": job_id}


@router.get("/{job_id}/results")
async def get_job_results(
    job_id: str,
    format: str = Query("json"),
    request: Request = None,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    job = await get_job(db, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    is_admin = request.state.user_role == "admin"
    if not is_admin and job["user_id"] != request.state.user_id:
        raise HTTPException(403, "Access denied")

    leads = await get_leads_by_job(db, job_id)

    if format == "csv":
        output = io.StringIO()
        if leads:
            writer = csv.DictWriter(output, fieldnames=leads[0].keys())
            writer.writeheader()
            writer.writerows(leads)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=job_{job_id}.csv"},
        )

    return {"results": leads, "total": len(leads), "job_id": job_id}
