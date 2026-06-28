"""Runtime config management endpoint (admin only)."""

import logging
import os

from fastapi import APIRouter, Depends, Request

from ..deps import get_db
from ..middleware.auth import require_admin
from ..models import ConfigResponse, ConfigUpdate
from ..store import log_audit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/config", tags=["config"])

_config_overrides: dict[str, str | int | float | bool] = {}


def _read_config() -> dict:
    return {
        "batch_size": int(os.getenv("BATCH_SIZE", "5")),
        "cooldown_sec": float(os.getenv("COOLDOWN_SEC", "8")),
        "mem_limit_mb": int(os.getenv("MEM_LIMIT_MB", "8192")),
        "cpu_limit_percent": int(os.getenv("CPU_LIMIT_PERCENT", "50")),
        "max_retries": int(os.getenv("MAX_RETRIES", "2")),
        "headless": os.getenv("HEADLESS", "true").lower() == "true",
        "max_job_duration_minutes": int(
            os.getenv("MAX_JOB_DURATION_MINUTES", "30")
        ),
        "disk_usage_warn_percent": int(
            os.getenv("DISK_USAGE_WARN_PERCENT", "80")
        ),
        "disk_usage_limit_percent": int(
            os.getenv("DISK_USAGE_LIMIT_PERCENT", "90")
        ),
    }


@router.get("", response_model=ConfigResponse)
async def get_config(
    request: Request,
    admin: dict = Depends(require_admin),
):
    cfg = _read_config()
    cfg.update(_config_overrides)
    return cfg


@router.patch("", response_model=ConfigResponse)
async def update_config(
    body: ConfigUpdate,
    request: Request,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    updates = body.model_dump(exclude_none=True)
    for key, value in updates.items():
        _config_overrides[key] = value

    await log_audit(
        db, request.state.user_id, "config.update",
        details=str(updates),
    )
    logger.info("Config updated by %s: %s", request.state.username, updates)

    cfg = _read_config()
    cfg.update(_config_overrides)
    return cfg
