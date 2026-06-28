"""Results query engine: filters, search, dedup, stats, export."""

import csv
import io
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from api.deps import get_db
from api.middleware.auth import require_user
from api.models import LeadResponse, LeadsPage
from api.store import get_lead_stats, get_leads_by_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/results", tags=["results"])


@router.get("", response_model=LeadsPage)
async def list_results(
    request: Request,
    keyword: str | None = None,
    job_id: str | None = None,
    phone_not_null: bool = False,
    website_not_null: bool = False,
    rating_min: float | None = None,
    review_count_min: int | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    """GET /api/v1/results - Leads with filters."""
    is_admin = request.state.user_role == "admin"
    uid = None if is_admin else request.state.user_id
    return await get_leads_by_user(
        db, uid, keyword=keyword, job_id=job_id,
        phone_not_null=phone_not_null, website_not_null=website_not_null,
        rating_min=rating_min, review_count_min=review_count_min,
        search=search, page=page, limit=limit,
    )


@router.get("/stats")
async def results_stats(
    request: Request,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    """GET /api/v1/results/stats - Aggregates."""
    is_admin = request.state.user_role == "admin"
    uid = None if is_admin else request.state.user_id
    if uid is None:
        raise HTTPException(400, "Admin stats not supported via this endpoint")
    return await get_lead_stats(db, uid)


@router.get("/export")
async def export_results(
    request: Request,
    format: str = Query("json"),
    keyword: str | None = None,
    job_id: str | None = None,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    """GET /api/v1/results/export - CSV or JSON."""
    is_admin = request.state.user_role == "admin"
    uid = None if is_admin else request.state.user_id
    if uid is None:
        raise HTTPException(400, "Admin export not supported via this endpoint")
    result = await get_leads_by_user(
        db, uid, keyword=keyword, job_id=job_id,
        page=1, limit=100000,
    )
    leads = result["results"]

    if format == "csv":
        output = io.StringIO()
        if leads:
            writer = csv.DictWriter(output, fieldnames=leads[0].keys())
            writer.writeheader()
            writer.writerows(leads)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
        )
    return {"results": leads, "total": len(leads)}


@router.get("/search")
async def search_results(
    request: Request,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    """GET /api/v1/results/search - Full-text."""
    is_admin = request.state.user_role == "admin"
    uid = None if is_admin else request.state.user_id
    if uid is None:
        raise HTTPException(400, "Admin search not supported via this endpoint")
    return await get_leads_by_user(db, uid, search=q, page=page, limit=limit)


@router.get("/{result_id}", response_model=LeadResponse)
async def get_result(
    result_id: int,
    request: Request,
    user: dict = Depends(require_user),
    db=Depends(get_db),
):
    """GET /api/v1/results/{id} - Single lead."""
    is_admin = request.state.user_role == "admin"
    cursor = await db.execute(
        "SELECT id, job_id, user_id, keyword, name, address, phone, website, "
        "rating, review_count, scraped_at FROM leads WHERE id = ?",
        (result_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(404, "Lead not found")
    from api.store import _row_to_lead
    lead = _row_to_lead(row)
    if not is_admin and lead["user_id"] != request.state.user_id:
        raise HTTPException(403, "Access denied")
    return lead
