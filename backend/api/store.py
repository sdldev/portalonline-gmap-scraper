"""SQLite persistence layer for PortalOnline GMap Scraper API."""

import logging
import secrets
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH: str = "data/portalonline.db"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _uid() -> str:
    return uuid.uuid4().hex[:12]


async def init_db(db_path: str = DB_PATH) -> aiosqlite.Connection:
    """Initialize database, create tables, and enable WAL mode."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(db_path)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    await db.execute("PRAGMA busy_timeout=5000")

    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id      TEXT PRIMARY KEY,
            username     TEXT NOT NULL UNIQUE,
            role         TEXT NOT NULL DEFAULT 'user',
            api_key      TEXT NOT NULL UNIQUE,
            password_hash TEXT,
            active       INTEGER NOT NULL DEFAULT 1,
            webhook_url  TEXT,
            webhook_events TEXT DEFAULT '["job.completed","job.failed"]',
            created_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS jobs (
            job_id       TEXT PRIMARY KEY,
            user_id      TEXT NOT NULL REFERENCES users(user_id),
            keyword      TEXT NOT NULL,
            location     TEXT,
            query        TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'queued',
            target       INTEGER NOT NULL DEFAULT 25,
            smart        INTEGER NOT NULL DEFAULT 1,
            queue_position INTEGER,
            leads_collected INTEGER NOT NULL DEFAULT 0,
            leads_total  INTEGER NOT NULL DEFAULT 0,
            error        TEXT,
            created_at   TEXT NOT NULL,
            started_at   TEXT,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS leads (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id       TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
            user_id      TEXT NOT NULL REFERENCES users(user_id),
            keyword      TEXT NOT NULL,
            name         TEXT NOT NULL,
            address      TEXT NOT NULL DEFAULT '',
            phone        TEXT NOT NULL DEFAULT 'N/A',
            website      TEXT NOT NULL DEFAULT 'N/A',
            rating       TEXT NOT NULL DEFAULT 'N/A',
            review_count TEXT NOT NULL DEFAULT 'N/A',
            scraped_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL REFERENCES users(user_id),
            action      TEXT NOT NULL,
            target_type TEXT,
            target_id   TEXT,
            details     TEXT,
            ip_address  TEXT,
            created_at  TEXT NOT NULL
        );
    """)

    # Migration: add password_hash column if missing
    try:
        await db.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        await db.commit()
    except Exception:
        pass  # Column already exists

    await _create_indexes(db)
    return db


async def _create_indexes(db: aiosqlite.Connection) -> None:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key)",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs(queue_position)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_leads_job_id ON leads(job_id)",
        "CREATE INDEX IF NOT EXISTS idx_leads_user_id ON leads(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_leads_keyword ON leads(keyword)",
        "CREATE INDEX IF NOT EXISTS idx_leads_dedup ON leads(name, address)",
        "CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)",
        "CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC)",
    ]
    for idx in indexes:
        await db.execute(idx)
    await db.commit()


# --- User CRUD ---


async def create_user(
    db: aiosqlite.Connection,
    username: str,
    role: str = "user",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Create a new user with auto-generated ID and API key."""
    user_id = _uid()
    key = api_key or f"pk_{_uid()}{_uid()}"
    now = _now()
    await db.execute(
        "INSERT INTO users (user_id, username, role, api_key, active, created_at) "
        "VALUES (?, ?, ?, ?, 1, ?)",
        (user_id, username, role, key, now),
    )
    await db.commit()
    return {
        "user_id": user_id,
        "username": username,
        "role": role,
        "api_key": key,
        "active": True,
        "created_at": now,
    }


async def get_user_by_api_key(
    db: aiosqlite.Connection, api_key: str
) -> dict[str, Any] | None:
    """Look up a user by their API key. Returns None if not found."""
    async with db.execute(
        "SELECT user_id, username, role, api_key, active, webhook_url, "
        "webhook_events, created_at FROM users WHERE api_key = ?",
        (api_key,),
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_user(row)


async def get_user_by_id(
    db: aiosqlite.Connection, user_id: str
) -> dict[str, Any] | None:
    """Look up a user by their unique ID. Returns None if not found."""
    async with db.execute(
        "SELECT user_id, username, role, api_key, active, webhook_url, "
        "webhook_events, created_at FROM users WHERE user_id = ?",
        (user_id,),
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_user(row)


async def list_users(db: aiosqlite.Connection) -> list[dict[str, Any]]:
    """Return all users ordered by creation date (newest first)."""
    async with db.execute(
        "SELECT user_id, username, role, api_key, active, webhook_url, "
        "webhook_events, created_at FROM users ORDER BY created_at DESC"
    ) as cursor:
        rows = await cursor.fetchall()
    return [_row_to_user(r) for r in rows]


async def update_user(
    db: aiosqlite.Connection,
    user_id: str,
    username: str | None = None,
    role: str | None = None,
    active: bool | None = None,
    webhook_url: str | None = None,
    webhook_events: str | None = None,
) -> dict[str, Any] | None:
    """Partially update user fields (username, role, active, webhook)."""
    fields = []
    values: list[Any] = []
    if username is not None:
        fields.append("username = ?")
        values.append(username)
    if role is not None:
        fields.append("role = ?")
        values.append(role)
    if active is not None:
        fields.append("active = ?")
        values.append(int(active))
    if webhook_url is not None:
        fields.append("webhook_url = ?")
        values.append(webhook_url)
    if webhook_events is not None:
        fields.append("webhook_events = ?")
        values.append(webhook_events)
    if not fields:
        return await get_user_by_id(db, user_id)
    values.append(user_id)
    await db.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?", values)
    await db.commit()
    return await get_user_by_id(db, user_id)


async def delete_user(db: aiosqlite.Connection, user_id: str) -> bool:
    """Delete a user by ID. Returns True if deleted, False if not found."""
    cursor = await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    await db.commit()
    return cursor.rowcount > 0


def _row_to_user(row: tuple) -> dict[str, Any]:
    return {
        "user_id": row[0],
        "username": row[1],
        "role": row[2],
        "api_key": row[3],
        "active": bool(row[4]),
        "webhook_url": row[5],
        "webhook_events": row[6],
        "created_at": row[7],
    }


# --- Job CRUD ---


async def create_job(
    db: aiosqlite.Connection,
    user_id: str,
    keyword: str,
    location: str | None,
    query: str,
    target: int = 25,
    smart: bool = True,
    queue_position: int | None = None,
) -> dict[str, Any]:
    """Create a new scraping job with queued status and optional queue position."""
    job_id = _uid()
    now = _now()
    await db.execute(
        "INSERT INTO jobs (job_id, user_id, keyword, location, query, status, "
        "target, smart, queue_position, created_at) "
        "VALUES (?, ?, ?, ?, ?, 'queued', ?, ?, ?, ?)",
        (
            job_id,
            user_id,
            keyword,
            location,
            query,
            target,
            int(smart),
            queue_position,
            now,
        ),
    )
    await db.commit()
    return await get_job(db, job_id)


async def get_job(db: aiosqlite.Connection, job_id: str) -> dict[str, Any] | None:
    """Fetch a job by ID, including the owner username via JOIN."""
    async with db.execute(
        "SELECT j.job_id, j.user_id, u.username, j.keyword, j.location, j.query, "
        "j.status, j.target, j.smart, j.queue_position, j.leads_collected, "
        "j.leads_total, j.error, j.created_at, j.started_at, j.completed_at "
        "FROM jobs j JOIN users u ON j.user_id = u.user_id WHERE j.job_id = ?",
        (job_id,),
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_job(row)


async def list_jobs(
    db: aiosqlite.Connection,
    user_id: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, Any]:
    """List jobs with pagination, user isolation, and optional filters."""
    conditions = []
    params: list[Any] = []
    if user_id:
        conditions.append("j.user_id = ?")
        params.append(user_id)
    if status:
        conditions.append("j.status = ?")
        params.append(status)
    if keyword:
        conditions.append("j.keyword LIKE ?")
        params.append(f"%{keyword}%")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    offset = (page - 1) * limit

    async with db.execute(f"SELECT COUNT(*) FROM jobs j {where}", params) as cursor:
        total = (await cursor.fetchone())[0]

    async with db.execute(
        f"SELECT j.job_id, j.user_id, u.username, j.keyword, j.location, j.query, "
        f"j.status, j.target, j.smart, j.queue_position, j.leads_collected, "
        f"j.leads_total, j.error, j.created_at, j.started_at, j.completed_at "
        f"FROM jobs j JOIN users u ON j.user_id = u.user_id "
        f"{where} ORDER BY j.created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ) as cursor:
        rows = await cursor.fetchall()

    return {
        "jobs": [_row_to_job(r) for r in rows],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, (total + limit - 1) // limit),
    }


async def update_job_status(
    db: aiosqlite.Connection,
    job_id: str,
    status: str,
    error: str | None = None,
    leads_collected: int | None = None,
    leads_total: int | None = None,
) -> None:
    """Update job status with optional error, lead counts, and timestamps."""
    fields = ["status = ?"]
    values: list[Any] = [status]
    if error is not None:
        fields.append("error = ?")
        values.append(error)
    if leads_collected is not None:
        fields.append("leads_collected = ?")
        values.append(leads_collected)
    if leads_total is not None:
        fields.append("leads_total = ?")
        values.append(leads_total)
    if status == "running":
        fields.append("started_at = ?")
        values.append(_now())
    if status in ("completed", "failed", "cancelled"):
        fields.append("completed_at = ?")
        values.append(_now())
    values.append(job_id)
    await db.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE job_id = ?", values)
    await db.commit()


async def cancel_job(db: aiosqlite.Connection, job_id: str) -> dict[str, Any] | None:
    """Cancel a job by setting status to cancelled."""
    job = await get_job(db, job_id)
    if job is None:
        return None
    await update_job_status(db, job_id, "cancelled")
    return await get_job(db, job_id)


async def delete_job(db: aiosqlite.Connection, job_id: str) -> bool:
    """Delete a job and all its leads. Returns True if deleted."""
    job = await get_job(db, job_id)
    if job is None:
        return False
    await db.execute("DELETE FROM leads WHERE job_id = ?", (job_id,))
    await db.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
    await db.commit()
    return True


def _row_to_job(row: tuple) -> dict[str, Any]:
    return {
        "job_id": row[0],
        "user_id": row[1],
        "username": row[2],
        "keyword": row[3],
        "location": row[4],
        "query": row[5],
        "status": row[6],
        "target": row[7],
        "smart": bool(row[8]),
        "queue_position": row[9],
        "leads_collected": row[10],
        "leads_total": row[11],
        "error": row[12],
        "created_at": row[13],
        "started_at": row[14],
        "completed_at": row[15],
    }


# --- Lead Operations ---


async def insert_leads_batch(
    db: aiosqlite.Connection,
    leads: list[dict[str, Any]],
) -> int:
    """Insert leads with dedup check on (name, address) normalization."""
    inserted = 0
    for lead in leads:
        name = (lead.get("name") or "").strip().lower()
        address = (lead.get("address") or "").strip().lower()
        async with db.execute(
            "SELECT id FROM leads WHERE LOWER(name) = ? AND LOWER(address) = ? "
            "AND job_id = ?",
            (name, address, lead["job_id"]),
        ) as cursor:
            existing = await cursor.fetchone()
        if existing:
            continue
        await db.execute(
            "INSERT INTO leads (job_id, user_id, keyword, name, address, phone, "
            "website, rating, review_count, scraped_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                lead["job_id"],
                lead["user_id"],
                lead["keyword"],
                lead.get("name", ""),
                lead.get("address", ""),
                lead.get("phone", "N/A"),
                lead.get("website", "N/A"),
                lead.get("rating", "N/A"),
                lead.get("review_count", "N/A"),
                _now(),
            ),
        )
        inserted += 1
    await db.commit()
    return inserted


async def get_leads_by_job(
    db: aiosqlite.Connection, job_id: str
) -> list[dict[str, Any]]:
    """Return all leads belonging to a specific job, ordered by ID."""
    async with db.execute(
        "SELECT id, job_id, user_id, keyword, name, address, phone, website, "
        "rating, review_count, scraped_at FROM leads WHERE job_id = ? "
        "ORDER BY id",
        (job_id,),
    ) as cursor:
        rows = await cursor.fetchall()
    return [_row_to_lead(r) for r in rows]


async def get_leads_by_user(
    db: aiosqlite.Connection,
    user_id: str,
    keyword: str | None = None,
    job_id: str | None = None,
    phone_not_null: bool | None = None,
    website_not_null: bool | None = None,
    rating_min: float | None = None,
    review_count_min: int | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 50,
) -> dict[str, Any]:
    """Query leads with filters (keyword, phone, rating, search) and pagination."""
    conditions = ["l.user_id = ?"]
    params: list[Any] = [user_id]
    if keyword:
        conditions.append("l.keyword = ?")
        params.append(keyword)
    if job_id:
        conditions.append("l.job_id = ?")
        params.append(job_id)
    if phone_not_null:
        conditions.append("l.phone != 'N/A' AND l.phone != ''")
    if website_not_null:
        conditions.append("l.website != 'N/A' AND l.website != ''")
    if rating_min is not None:
        conditions.append("CAST(l.rating AS REAL) >= ?")
        params.append(rating_min)
    if review_count_min is not None:
        conditions.append("CAST(l.review_count AS INTEGER) >= ?")
        params.append(review_count_min)
    if search:
        conditions.append("(l.name LIKE ? OR l.address LIKE ? OR l.phone LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    where = f"WHERE {' AND '.join(conditions)}"
    offset = (page - 1) * limit

    async with db.execute(f"SELECT COUNT(*) FROM leads l {where}", params) as cursor:
        total = (await cursor.fetchone())[0]

    async with db.execute(
        f"SELECT id, job_id, user_id, keyword, name, address, phone, website, "
        f"rating, review_count, scraped_at FROM leads l {where} "
        f"ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ) as cursor:
        rows = await cursor.fetchall()

    return {
        "results": [_row_to_lead(r) for r in rows],
        "total": total,
        "page": page,
        "limit": limit,
    }


async def get_lead_stats(db: aiosqlite.Connection, user_id: str) -> dict[str, Any]:
    """Return aggregate stats: total leads, unique keywords, phone/website coverage."""
    async with db.execute(
        "SELECT "
        "COUNT(*) as total_leads, "
        "COUNT(DISTINCT keyword) as unique_keywords, "
        "SUM(CASE WHEN phone != 'N/A' AND phone != '' THEN 1 ELSE 0 END) "
        "as with_phone, "
        "SUM(CASE WHEN website != 'N/A' AND website != '' THEN 1 ELSE 0 END) "
        "as with_website, "
        "SUM(CASE WHEN rating != 'N/A' AND rating != '' THEN 1 ELSE 0 END) "
        "as with_rating, "
        "AVG(CASE WHEN rating != 'N/A' AND rating != '' "
        "THEN CAST(rating AS REAL) END) as avg_rating "
        "FROM leads WHERE user_id = ?",
        (user_id,),
    ) as cursor:
        row = await cursor.fetchone()
    return {
        "total_leads": row[0] or 0,
        "unique_keywords": row[1] or 0,
        "leads_with_phone": row[2] or 0,
        "leads_with_website": row[3] or 0,
        "leads_with_rating": row[4] or 0,
        "avg_rating": round(row[5] or 0, 2),
    }


def _row_to_lead(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "job_id": row[1],
        "user_id": row[2],
        "keyword": row[3],
        "name": row[4],
        "address": row[5],
        "phone": row[6],
        "website": row[7],
        "rating": row[8],
        "review_count": row[9],
        "scraped_at": row[10],
    }


# --- Audit Operations ---


async def log_audit(
    db: aiosqlite.Connection,
    user_id: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    details: str | None = None,
    ip_address: str | None = None,
) -> None:
    """Write an audit log entry with user, action, target, and optional IP."""
    await db.execute(
        "INSERT INTO audit_logs (user_id, action, target_type, target_id, "
        "details, ip_address, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, action, target_type, target_id, details, ip_address, _now()),
    )
    await db.commit()


async def get_audit_logs(
    db: aiosqlite.Connection,
    user_id: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    page: int = 1,
    limit: int = 50,
) -> dict[str, Any]:
    """Fetch audit logs with filters (user, action, date range) and pagination."""
    conditions = []
    params: list[Any] = []
    if user_id:
        conditions.append("a.user_id = ?")
        params.append(user_id)
    if action:
        conditions.append("a.action = ?")
        params.append(action)
    if target_type:
        conditions.append("a.target_type = ?")
        params.append(target_type)
    if from_date:
        conditions.append("a.created_at >= ?")
        params.append(from_date)
    if to_date:
        conditions.append("a.created_at <= ?")
        params.append(to_date)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    offset = (page - 1) * limit

    async with db.execute(
        f"SELECT COUNT(*) FROM audit_logs a {where}", params
    ) as cursor:
        total = (await cursor.fetchone())[0]

    async with db.execute(
        f"SELECT a.id, a.user_id, u.username, a.action, a.target_type, "
        f"a.target_id, a.details, a.ip_address, a.created_at "
        f"FROM audit_logs a JOIN users u ON a.user_id = u.user_id "
        f"{where} ORDER BY a.created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ) as cursor:
        rows = await cursor.fetchall()

    return {
        "logs": [_row_to_audit(r) for r in rows],
        "total": total,
        "page": page,
        "limit": limit,
    }


def _row_to_audit(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "user_id": row[1],
        "username": row[2],
        "action": row[3],
        "target_type": row[4],
        "target_id": row[5],
        "details": row[6],
        "ip_address": row[7],
        "created_at": row[8],
    }


# --- Queue Operations ---


async def get_queue(
    db: aiosqlite.Connection, user_id: str | None = None
) -> dict[str, Any]:
    """Return active job and queued jobs, optionally filtered by user."""
    if user_id:
        async with db.execute(
            "SELECT j.job_id, j.user_id, u.username, j.keyword, j.location, "
            "j.status, j.queue_position, j.created_at, j.started_at "
            "FROM jobs j JOIN users u ON j.user_id = u.user_id "
            "WHERE j.user_id = ? AND j.status IN ('queued', 'running') "
            "ORDER BY j.queue_position ASC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
    else:
        async with db.execute(
            "SELECT j.job_id, j.user_id, u.username, j.keyword, j.location, "
            "j.status, j.queue_position, j.created_at, j.started_at "
            "FROM jobs j JOIN users u ON j.user_id = u.user_id "
            "WHERE j.status IN ('queued', 'running') "
            "ORDER BY j.queue_position ASC"
        ) as cursor:
            rows = await cursor.fetchall()

    active_job = None
    queued: list[dict[str, Any]] = []
    for r in rows:
        item = {
            "job_id": r[0],
            "user_id": r[1],
            "username": r[2],
            "keyword": r[3],
            "location": r[4],
            "status": r[5],
            "queue_position": r[6],
            "created_at": r[7],
            "started_at": r[8],
        }
        if r[5] == "running":
            active_job = item
        else:
            queued.append(item)
    return {"active_job": active_job, "queue": queued}


async def get_next_queued(db: aiosqlite.Connection) -> dict[str, Any] | None:
    """Return the next queued job (lowest queue_position) or None."""
    async with db.execute(
        "SELECT j.job_id, j.user_id, u.username, j.keyword, j.location, "
        "j.query, j.status, j.target, j.smart, j.queue_position, "
        "j.leads_collected, j.leads_total, j.error, j.created_at, "
        "j.started_at, j.completed_at "
        "FROM jobs j JOIN users u ON j.user_id = u.user_id "
        "WHERE j.status = 'queued' ORDER BY j.queue_position ASC LIMIT 1"
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_job(row)


async def get_queue_position(db: aiosqlite.Connection) -> int:
    """Return the next available queue position (MAX + 1) for queued jobs."""
    async with db.execute(
        "SELECT COALESCE(MAX(queue_position), 0) + 1 FROM jobs WHERE status = 'queued'"
    ) as cursor:
        row = await cursor.fetchone()
    return row[0]


async def reindex_queue(db: aiosqlite.Connection) -> None:
    """Reassign sequential queue positions to all queued jobs."""
    async with db.execute(
        "SELECT job_id FROM jobs WHERE status = 'queued' ORDER BY queue_position ASC"
    ) as cursor:
        job_ids = [row[0] for row in await cursor.fetchall()]
    for idx, job_id in enumerate(job_ids, start=1):
        await db.execute(
            "UPDATE jobs SET queue_position = ? WHERE job_id = ?",
            (idx, job_id),
        )
    await db.commit()


async def get_db_stats(db: aiosqlite.Connection) -> dict[str, Any]:
    """Return database stats: row counts, file size, path."""
    tables = ["users", "jobs", "leads", "audit_logs"]
    stats: dict[str, int] = {}
    for table in tables:
        async with db.execute(f"SELECT COUNT(*) FROM {table}") as cursor:
            stats[table] = (await cursor.fetchone())[0]

    file_size = Path(DB_PATH).stat().st_size if Path(DB_PATH).exists() else 0

    return {
        "row_counts": stats,
        "db_size_bytes": file_size,
        "db_size_mb": round(file_size / (1024 * 1024), 2),
        "db_path": DB_PATH,
    }


async def run_cleanup(
    db: aiosqlite.Connection, older_than_days: int = 90
) -> dict[str, Any]:
    """Delete old completed/failed/cancelled jobs and their leads, then vacuum."""
    cutoff = datetime.now(UTC).isoformat()

    async with db.execute(
        "SELECT COUNT(*) FROM jobs WHERE status IN ('completed','failed','cancelled') "
        "AND completed_at < ?",
        (cutoff,),
    ) as cursor:
        deleted_jobs = (await cursor.fetchone())[0]

    async with db.execute(
        "SELECT COUNT(*) FROM leads WHERE job_id IN "
        "(SELECT job_id FROM jobs WHERE status IN ('completed','failed','cancelled') "
        "AND completed_at < ?)",
        (cutoff,),
    ) as cursor:
        deleted_leads = (await cursor.fetchone())[0]

    await db.execute(
        "DELETE FROM leads WHERE job_id IN "
        "(SELECT job_id FROM jobs WHERE status IN ('completed','failed','cancelled') "
        "AND completed_at < ?)",
        (cutoff,),
    )
    await db.execute(
        "DELETE FROM jobs WHERE status IN ('completed','failed','cancelled') "
        "AND completed_at < ?",
        (cutoff,),
    )

    async with db.execute(
        "SELECT COUNT(*) FROM audit_logs WHERE created_at < ?", (cutoff,)
    ) as cursor:
        deleted_audit = (await cursor.fetchone())[0]
    await db.execute("DELETE FROM audit_logs WHERE created_at < ?", (cutoff,))

    file_size_before = Path(DB_PATH).stat().st_size if Path(DB_PATH).exists() else 0
    await db.execute("PRAGMA incremental_vacuum")
    await db.commit()
    file_size_after = Path(DB_PATH).stat().st_size if Path(DB_PATH).exists() else 0

    return {
        "deleted_jobs": deleted_jobs,
        "deleted_leads": deleted_leads,
        "deleted_audit_logs": deleted_audit,
        "db_size_before_mb": round(file_size_before / (1024 * 1024), 2),
        "db_size_after_mb": round(file_size_after / (1024 * 1024), 2),
    }


# --- Auth / Password Functions ---


async def get_user_by_username(
    db: aiosqlite.Connection, username: str
) -> dict[str, Any] | None:
    """Look up a user by username. Returns None if not found."""
    async with db.execute(
        "SELECT user_id, username, role, api_key, password_hash, active, "
        "webhook_url, webhook_events, created_at FROM users WHERE username = ?",
        (username,),
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_user_with_password(row)


async def create_user_with_password(
    db: aiosqlite.Connection,
    username: str,
    password: str,
    role: str = "user",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Create user with bcrypt password hash."""
    import bcrypt

    user_id = _uid()
    key = api_key or f"pk_{_uid()}{_uid()}"
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    now = _now()
    await db.execute(
        "INSERT INTO users (user_id, username, role, api_key, password_hash, "
        "active, created_at) VALUES (?, ?, ?, ?, ?, 1, ?)",
        (user_id, username, role, key, password_hash, now),
    )
    await db.commit()
    return {
        "user_id": user_id,
        "username": username,
        "role": role,
        "api_key": key,
        "active": True,
        "password_hash": password_hash,
        "webhook_url": None,
        "webhook_events": '["job.completed","job.failed"]',
        "created_at": now,
    }


async def verify_password(
    db: aiosqlite.Connection, username: str, password: str
) -> dict[str, Any] | None:
    """Verify username + password. Returns user dict or None."""
    import bcrypt

    user = await get_user_by_username(db, username)
    if user is None:
        return None
    if not user.get("password_hash"):
        return None
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return None
    if not user["active"]:
        return None
    return user


async def update_user_password(
    db: aiosqlite.Connection, user_id: str, new_password: str
) -> str:
    """Set a new bcrypt password hash for user. Returns the plaintext password."""
    import bcrypt

    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    await db.execute(
        "UPDATE users SET password_hash = ? WHERE user_id = ?",
        (password_hash, user_id),
    )
    await db.commit()
    return new_password


async def regenerate_api_key(db: aiosqlite.Connection, user_id: str) -> str | None:
    """Generate a new API key for user. Returns new key or None if user not found."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        return None
    new_key = f"pk_{_uid()}{_uid()}"
    await db.execute(
        "UPDATE users SET api_key = ? WHERE user_id = ?",
        (new_key, user_id),
    )
    await db.commit()
    return new_key


async def get_dashboard_stats(db: aiosqlite.Connection) -> dict[str, Any]:
    """Return dashboard aggregate stats: user count, job counts, recent jobs."""
    async with db.execute("SELECT COUNT(*) FROM users") as cursor:
        total_users = (await cursor.fetchone())[0]

    async with db.execute("SELECT COUNT(*) FROM jobs") as cursor:
        total_jobs = (await cursor.fetchone())[0]

    async with db.execute("SELECT COUNT(*) FROM leads") as cursor:
        total_leads = (await cursor.fetchone())[0]

    async with db.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'running'"
    ) as cursor:
        active_jobs = (await cursor.fetchone())[0]

    async with db.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'queued'"
    ) as cursor:
        queued_jobs = (await cursor.fetchone())[0]

    async with db.execute(
        "SELECT j.job_id, j.user_id, u.username, j.keyword, j.location, j.query, "
        "j.status, j.target, j.smart, j.queue_position, j.leads_collected, "
        "j.leads_total, j.error, j.created_at, j.started_at, j.completed_at "
        "FROM jobs j JOIN users u ON j.user_id = u.user_id "
        "ORDER BY j.created_at DESC LIMIT 10"
    ) as cursor:
        rows = await cursor.fetchall()

    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_leads": total_leads,
        "active_jobs": active_jobs,
        "queued_jobs": queued_jobs,
        "recent_jobs": [_row_to_job(r) for r in rows],
    }


async def get_stats_counts(db: aiosqlite.Connection) -> dict[str, Any]:
    """Return dashboard counts only (no recent_jobs). Lightweight alternative."""
    async with db.execute("SELECT COUNT(*) FROM users") as cursor:
        total_users = (await cursor.fetchone())[0]

    async with db.execute("SELECT COUNT(*) FROM jobs") as cursor:
        total_jobs = (await cursor.fetchone())[0]

    async with db.execute("SELECT COUNT(*) FROM leads") as cursor:
        total_leads = (await cursor.fetchone())[0]

    async with db.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'running'"
    ) as cursor:
        active_jobs = (await cursor.fetchone())[0]

    async with db.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'queued'"
    ) as cursor:
        queued_jobs = (await cursor.fetchone())[0]

    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_leads": total_leads,
        "active_jobs": active_jobs,
        "queued_jobs": queued_jobs,
    }


def _row_to_user_with_password(row: tuple) -> dict[str, Any]:
    return {
        "user_id": row[0],
        "username": row[1],
        "role": row[2],
        "api_key": row[3],
        "password_hash": row[4],
        "active": bool(row[5]),
        "webhook_url": row[6],
        "webhook_events": row[7],
        "created_at": row[8],
    }


def generate_random_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password."""
    return secrets.token_urlsafe(length)[:length]
