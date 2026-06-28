"""Pydantic models and validators for PortalOnline GMap Scraper API."""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

# --- User Models ---

class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    role: str = Field(default="user")
    webhook_url: str | None = Field(default=None, max_length=500)
    webhook_events: list[str] | None = Field(default=None)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate: only a-z, 0-9, underscore. Max 50 chars."""
        v = v.strip()
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError("username: only a-z, 0-9, underscore allowed")
        return v


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    role: str | None = None
    active: bool | None = None
    webhook_url: str | None = Field(default=None, max_length=500)
    webhook_events: list[str] | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError("username: only a-z, 0-9, underscore allowed")
        return v


class UserResponse(BaseModel):
    user_id: str
    username: str
    role: str
    api_key: str
    active: bool
    webhook_url: str | None = None
    webhook_events: str | None = None
    created_at: str


# --- Job Models ---

class JobCreate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=100)
    target: int = Field(default=25, ge=1, le=500)
    smart: bool = True
    category_variations: list[str] | None = Field(default=None, max_length=10)
    timeout_minutes: int | None = Field(default=None, ge=1, le=120)

    @field_validator("keyword")
    @classmethod
    def validate_keyword(cls, v: str) -> str:
        """Sanitize: strip blocked chars, trim whitespace. Max 200 chars."""
        v = v.strip()
        blocked = ["<", ">", "\"", "\'", ";", "--", "/*", "*/"]
        for c in blocked:
            v = v.replace(c, "")
        if not v:
            raise ValueError("keyword must not be empty after sanitization")
        return v

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str | None) -> str | None:
        """Sanitize: strip blocked chars. Returns None if empty. Max 100 chars."""
        if v is None:
            return v
        v = v.strip()
        blocked = ["<", ">", "\"", "\'", ";", "--", "/*", "*/"]
        for c in blocked:
            v = v.replace(c, "")
        return v if v else None

    @field_validator("category_variations")
    @classmethod
    def validate_variations(cls, v: list[str] | None) -> list[str] | None:
        """Validate: max 10 items, each max 100 chars."""
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("max 10 category variations")
        return [s[:100].strip() for s in v]


class JobResponse(BaseModel):
    job_id: str
    user_id: str
    username: str
    keyword: str
    location: str | None = None
    query: str
    status: str
    target: int
    smart: bool
    queue_position: int | None = None
    leads_collected: int
    leads_total: int
    error: str | None = None
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None


class JobProgress(BaseModel):
    leads_collected: int
    total_leads: int
    current_batch: int = 0
    status: str


class JobsPage(BaseModel):
    jobs: list[JobResponse]
    total: int
    page: int
    limit: int
    pages: int


# --- Queue Models ---

class QueuedItem(BaseModel):
    job_id: str
    user_id: str
    username: str
    keyword: str
    location: str | None = None
    status: str
    queue_position: int | None = None
    created_at: str
    started_at: str | None = None


class ActiveJob(BaseModel):
    job_id: str
    user_id: str
    username: str
    keyword: str
    location: str | None = None
    status: str
    queue_position: int | None = None
    created_at: str
    started_at: str | None = None


class QueueStatus(BaseModel):
    active_job: ActiveJob | None = None
    queue: list[QueuedItem] = []


# --- Lead Models ---

class LeadResponse(BaseModel):
    id: int
    job_id: str
    user_id: str
    keyword: str
    name: str
    address: str
    phone: str
    website: str
    rating: str
    review_count: str
    scraped_at: str


class LeadsPage(BaseModel):
    results: list[LeadResponse]
    total: int
    page: int
    limit: int


# --- Health & System Models ---

class SystemInfo(BaseModel):
    ram_used_mb: float
    ram_total_mb: float
    ram_percent: float
    cpu_percent: float
    disk_used_gb: float
    disk_total_gb: float
    disk_percent: float
    active_jobs: int
    queued_jobs: int
    uptime_seconds: float
    db_size_mb: float


class HealthResponse(BaseModel):
    status: str
    version: str
    db_connected: bool
    uptime_seconds: float


# --- Audit Models ---

class AuditLogResponse(BaseModel):
    id: int
    user_id: str
    username: str
    action: str
    target_type: str | None = None
    target_id: str | None = None
    details: str | None = None
    ip_address: str | None = None
    created_at: str


class AuditLogPage(BaseModel):
    logs: list[AuditLogResponse]
    total: int
    page: int
    limit: int


# --- Config Models ---

class ConfigResponse(BaseModel):
    batch_size: int
    cooldown_sec: float
    mem_limit_mb: int
    cpu_limit_percent: int
    max_retries: int
    headless: bool
    max_job_duration_minutes: int
    disk_usage_warn_percent: int
    disk_usage_limit_percent: int


class ConfigUpdate(BaseModel):
    batch_size: int | None = Field(default=None, ge=1, le=50)
    cooldown_sec: float | None = Field(default=None, ge=0, le=300)
    mem_limit_mb: int | None = Field(default=None, ge=256, le=32768)
    cpu_limit_percent: int | None = Field(default=None, ge=0, le=100)
    max_retries: int | None = Field(default=None, ge=0, le=10)
    headless: bool | None = None
    max_job_duration_minutes: int | None = Field(default=None, ge=1, le=120)
    disk_usage_warn_percent: int | None = Field(default=None, ge=0, le=100)
    disk_usage_limit_percent: int | None = Field(default=None, ge=0, le=100)


# --- Webhook Models ---

class WebhookConfig(BaseModel):
    url: str = Field(..., max_length=500)
    events: list[str] = Field(
        default=["job.completed", "job.failed"]
    )


# --- Error Models ---

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


# --- Cleanup / DB Stats Models ---

class CleanupRequest(BaseModel):
    older_than_days: int = Field(default=30, ge=1, le=365)


class CleanupResponse(BaseModel):
    deleted_jobs: int
    deleted_leads: int
    deleted_audit_logs: int
    db_size_before_mb: float
    db_size_after_mb: float


class DbStatsResponse(BaseModel):
    row_counts: dict[str, int]
    db_size_bytes: int
    db_size_mb: float
    db_path: str
