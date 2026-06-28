"""SSE streaming endpoint for real-time job progress."""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from api.deps import get_db, get_job_manager
from api.store import get_job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["sse"])


async def _auth_sse(
    request: Request,
    db=Depends(get_db),
    token: str | None = Query(default=None),
) -> dict:
    """Auth for SSE: token query param (EventSource can't set custom headers)."""
    from api.auth_utils import verify_token
    from api.store import get_user_by_api_key, get_user_by_id

    user = None

    if token:
        payload = verify_token(token)
        if payload:
            user = await get_user_by_id(db, payload["user_id"])

    if user is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = verify_token(auth_header.removeprefix("Bearer "))
            if payload:
                user = await get_user_by_id(db, payload["user_id"])

    if user is None:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            user = await get_user_by_api_key(db, api_key)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication")
    if not user["active"]:
        raise HTTPException(status_code=403, detail="User account is inactive")

    request.state.user_id = user["user_id"]
    request.state.user_role = user["role"]
    request.state.username = user["username"]
    return user


@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(
    job_id: str,
    request: Request,
    token: str | None = Query(default=None),
    user: dict = Depends(_auth_sse),
    db=Depends(get_db),
):
    """GET /api/v1/jobs/{id}/stream - SSE events."""
    job = await get_job(db, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    is_admin = request.state.user_role == "admin"
    if not is_admin and job["user_id"] != request.state.user_id:
        raise HTTPException(403, "Access denied")

    manager = get_job_manager(request)

    async def event_stream():
        """Async generator: heartbeat, status_change, completed."""
        last_status = job["status"]
        yield f"data: {json.dumps({'event': 'connected', 'job_id': job_id})}\n\n"

        while True:
            current = await get_job(db, job_id)
            if current is None:
                break

            new_status = current["status"]
            if new_status != last_status:
                yield (
                    "data: "
                    + json.dumps({
                        "event": "status_change",
                        "old": last_status,
                        "new": new_status,
                    })
                    + "\n\n"
                )
                last_status = new_status

            progress = manager.get_progress(job_id)
            if progress:
                yield f"data: {json.dumps({'event': 'progress', **progress})}\n\n"

            if new_status in ("completed", "failed", "cancelled"):
                yield (
                    "data: "
                    + json.dumps({"event": "completed", "status": new_status})
                    + "\n\n"
                )
                break

            yield f"data: {json.dumps({'event': 'heartbeat'})}\n\n"
            await asyncio.sleep(15)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
