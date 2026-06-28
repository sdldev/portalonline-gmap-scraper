# Phase 1: MVP Core Platform (Week 1-2)

**Goal**: Ship a minimal but complete platform — "walking skeleton" — that accepts scraping jobs via API, persists results to SQLite, provides basic job visibility, and enforces API-key auth with RBAC.

**Success Gate**: `POST /api/v1/jobs` → queue → scrape → `GET /api/v1/jobs/{id}/results?format=json` works end-to-end with auth.

---

## Workstreams & Tasks

### WS-1.1: Dependencies & Project Scaffold

| Task | File(s) | Description |
|------|---------|-------------|
| Add deps | `pyproject.toml` | Add `fastapi>=0.115.0`, `uvicorn[standard]>=0.34.0`, `pydantic>=2.0.0`, `aiosqlite>=0.20.0`, `httpx>=0.27.0` |
| Sync deps | — | Run `uv sync` |
| Create dirs | `portalonline_gmap_scraper/api/`, `api/routes/`, `api/middleware/`, `data/` | Directory scaffolding |
| Init packages | `api/__init__.py`, `api/routes/__init__.py`, `api/middleware/__init__.py` | Empty `__init__.py` files |
| Gitignore | `.gitignore` | Add `data/` directory |

### WS-1.2: SQLite Persistence Layer (`store.py`)

| Task | Description |
|------|-------------|
| `init_db()` | Create tables: `users`, `jobs`, `leads`, `audit_logs` with all indexes from PRD schema. Enable WAL mode. |
| User CRUD | `create_user()`, `get_user_by_api_key()`, `get_user_by_id()`, `list_users()`, `update_user()`, `delete_user()` |
| Job CRUD | `create_job()`, `get_job()`, `list_jobs()` (with user isolation + filters), `update_job_status()`, `cancel_job()` |
| Lead ops | `insert_leads_batch()` with dedup check (`name + address` normalization). `get_leads_by_job()`, `get_leads_by_user()`. |
| Audit ops | `log_audit()` — write to `audit_logs` table |
| Queue ops | `get_queue()` — ordered by `queue_position`, `get_next_queued()` — lowest `queue_position`, `reindex_queue()` after dequeue/remove |
| Build index | `create_indexes()` — all indexes from PRD schema |
| Tests | `tests/test_store.py` — CRUD for all tables, dedup logic, queue ordering |

**Schema reference** (from PRD):

```sql
-- users table
CREATE TABLE IF NOT EXISTS users (
    user_id      TEXT PRIMARY KEY,
    username     TEXT NOT NULL UNIQUE,
    role         TEXT NOT NULL DEFAULT 'user',
    api_key      TEXT NOT NULL UNIQUE,
    active       INTEGER NOT NULL DEFAULT 1,
    webhook_url  TEXT,
    webhook_events TEXT DEFAULT '["job.completed","job.failed"]',
    created_at   TEXT NOT NULL
);

-- jobs table
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

-- leads table
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

-- audit_logs table
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
```

### WS-1.3: Pydantic Models (`models.py`)

| Task | Description |
|------|-------------|
| User models | `UserCreate`, `UserUpdate`, `UserResponse` |
| Job models | `JobCreate` (keyword, location, target, smart, category_variations, timeout_minutes), `JobResponse` (includes queue_position, estimated_wait_minutes) |
| JobProgress | `JobProgress` — leads_collected, total_leads, current_batch, status |
| Queue models | `QueueStatus`, `ActiveJob`, `QueuedItem` |
| Lead models | `LeadResponse`, `LeadsPage` (results, total, page, limit) |
| Health models | `HealthResponse`, `SystemInfo` |
| Audit models | `AuditLogResponse`, `AuditLogPage` |
| Config models | `ConfigResponse`, `ConfigUpdate` |
| Error models | `ErrorResponse` — success: false, error: {code, message, existing_job_id?} |
| Validation | Pydantic `Field` validators: keyword max 200, location max 100, target min 1 max 500 |
| Sanitization | Custom validators for keyword/location (strip `<`, `>`, `"`, `'`, `;`, `--`, `/*`) |
| Tests | `tests/test_api_models.py` — validation edge cases, blocked chars, field limits |

### WS-1.4: API Key + RBAC Middleware (`middleware/auth.py`)

| Task | Description |
|------|-------------|
| `verify_api_key()` | Dependency: extract `X-API-Key` header, look up user in SQLite, attach `user_id` + `role` to request state |
| `require_admin()` | Dependency: check `request.state.role == "admin"`, raise 403 if not |
| `require_user()` | Dependency: check `request.state.user_id` is set, raise 401 if not |
| Default admin creation | On first startup (no users in DB), auto-create admin from `ADMIN_API_KEY` env var |
| Tests | `tests/test_auth.py` — valid key, invalid key, missing header, RBAC enforcement |

### WS-1.5: Input Sanitization (`middleware/sanitize.py`)

| Task | Description |
|------|-------------|
| Pydantic validators | `validate_keyword()`, `validate_location()`, `validate_username()` — strip blocked chars, trim whitespace |
| Field rules | keyword: alphanumeric+spaces+dash, max 200. location: alphanumeric+spaces+comma+dot, max 100. username: `a-z0-9_` only, max 50 |
| Category variations | Max 10 items, each max 100 chars, same sanitization as keyword |
| Tests | `tests/test_sanitize.py` — blocked chars, SQL injection patterns, empty strings, max length |

### WS-1.6: Job Manager (`job_manager.py`)

**Core class**: `JobManager` (singleton per app instance)

| Task | Description |
|------|-------------|
| `submit()` | Validate input → check duplicate → async insert to DB → if no active job, start immediately; else enqueue with `queue_position` |
| `cancel()` | RBAC: user cancels own, admin cancels any. If running: stop scraper, save partial leads, dequeue next. If queued: remove from queue, reindex. |
| `_dequeue_next()` | After job finishes: query next queued (ORDER BY queue_position ASC), set running, reindex remaining queue |
| `_run_job()` | Execute `scrape()`/`scrape_smart()` in background task. Batch-write leads to SQLite (with dedup). Update progress. Handle timeout. |
| Duplicate detection | Before `submit()`: check if user already has same `keyword + location` with status `queued`/`running`. Reject with `DUPLICATE_JOB` code. |
| Job timeout | `MAX_JOB_DURATION_MINUTES` (default 30). Background timer cancels job if exceeded. Saves partial results. Dequeues next. |
| Graceful shutdown | SIGTERM handler: mark running job failed ("Server shutting down"), close DB, exit. Registered via `asyncio` signal handlers. |
| Progress tracking | `dict[str, JobProgress]` updated per batch. Used by SSE (Phase 3) and `GET /api/v1/jobs/{id}`. |
| Tests | `tests/test_job_manager.py` — submit, duplicate detection, cancel, dequeue, timeout, graceful shutdown (mocked scraper) |

**Scraper Integration** — `_run_job()`:

```python
async def _run_job(self, job: Job) -> None:
    try:
        leads = await asyncio.to_thread(
            scrape, keyword=job.keyword, location=job.location,
            target=job.target,
            on_batch_complete=lambda batch: self._on_leads_batch(job.job_id, batch)
        )
    except Exception as e:
        await self.store.update_job_status(job.job_id, "failed", error=str(e))
    finally:
        await self._dequeue_next()
```

### WS-1.7: Route — Users (`routes/users.py`)

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/users` | POST | admin | Create user (generate API key if not provided) |
| `/api/v1/users` | GET | admin | List all users |
| `/api/v1/users/me` | GET | any | View own profile |
| `/api/v1/users/{user_id}` | GET | admin | Get user detail |
| `/api/v1/users/{user_id}` | PATCH | admin | Update user (role, active status) |
| `/api/v1/users/{user_id}` | DELETE | admin | Delete user |

Tests: `tests/test_routes_users.py`

### WS-1.8: Route — Jobs (`routes/jobs.py`)

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/jobs` | POST | any | Submit scraping job (with duplicate detection) |
| `/api/v1/jobs` | GET | any | List jobs (user: own, admin: all + filter by user_id) |
| `/api/v1/jobs/{job_id}` | GET | any | Job detail (includes queue_position, estimated_wait_minutes) |
| `/api/v1/jobs/{job_id}` | DELETE | any | Cancel job (RBAC: user own, admin any) |
| `/api/v1/jobs/{job_id}/results` | GET | any | Results JSON/CSV (query param: `format`) |

Tests: `tests/test_routes_jobs.py` — user isolation, duplicate detection, RBAC for cancel

### WS-1.9: Route — Health & System (`routes/health.py`)

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/health` | GET | public | Health check: 200 OK or 503 (DB connection check) |
| `/api/v1/system` | GET | any | Resource monitoring (RAM, CPU, disk, active jobs, uptime) |

Tests: `tests/test_routes_health.py`

### WS-1.10: FastAPI App Factory (`app.py`)

| Task | Description |
|------|-------------|
| `create_app()` | Factory function: create FastAPI instance with title, version, lifespan |
| Lifespan | Startup: init DB, create default admin, recover orphan jobs. Shutdown: cancel active job, close DB. |
| Middleware | Mount auth middleware globally. Mount sanitize validators. |
| Routes | Register all route modules (`users`, `jobs`, `health`) |
| CORS | Configurable via `CORS_ORIGINS` env var (Phase 3 polish, stubbed here) |
| OpenAPI | Auto-generated at `/docs` (Swagger) and `/redoc` |

### WS-1.11: Server Entry Point (`server.py`)

| Task | Description |
|------|-------------|
| Main | Import `create_app()`, configure Uvicorn on 0.0.0.0:9988 |
| Startup recovery | Reconstruct queue from DB: mark `status=running` jobs as `failed` ("Server restarted"), rebuild in-memory queue from `status=queued` ORDER BY `queue_position` |
| Default admin | If no users exist, create admin from `ADMIN_API_KEY` env var (or generate + log) |
| Signal handlers | SIGTERM/SIGINT → graceful shutdown (cancel active, close DB, exit) |
| CLI | `python -m portalonline_gmap_scraper.server` or as `__main__` |

### WS-1.12: Config Updates (`config.py`)

| Var | Default | Description |
|-----|---------|-------------|
| `API_PORT` | 9988 | Server port |
| `API_HOST` | 0.0.0.0 | Bind address |
| `ADMIN_API_KEY` | (required) | Admin API key for initial user creation |
| `MAX_JOB_DURATION_MINUTES` | 30 | Auto-cancel timeout |
| `MAX_TARGET_PER_JOB` | 500 | Cap lead target per job |
| `DATA_DIR` | `data` | SQLite file location |
| `CORS_ORIGINS` | `*` | CORS allowed origins (Phase 3) |

### WS-1.13: Tests (8 files)

| Test File | Coverage |
|-----------|----------|
| `tests/test_store.py` | All CRUD ops, dedup, queue ordering, WAL mode |
| `tests/test_api_models.py` | Pydantic validation, field limits, sanitization |
| `tests/test_job_manager.py` | Queue logic, duplicate detection, cancel, timeout, shutdown (mocked scraper) |
| `tests/test_routes_users.py` | User CRUD, admin RBAC enforcement |
| `tests/test_routes_jobs.py` | Job submit (immediate vs queued), user isolation, duplicate reject, cancel RBAC, results retrieval |
| `tests/test_routes_health.py` | Health 200/503, system endpoint |
| `tests/test_auth.py` | API key validation, missing header, invalid key, RBAC middleware |
| `tests/test_sanitize.py` | Blocked chars, SQL injection patterns, edge cases |

---

## Implementation Order (Day-by-Day)

### Week 1

| Day | Tasks | Files |
|-----|-------|-------|
| 1 | Add deps, scaffold dirs, init packages | `pyproject.toml`, `__init__.py` x 3, `.gitignore` |
| 2 | Build `store.py` — users + jobs + leads + audit_logs tables, indexes, WAL mode | `store.py` |
| 3 | Build `models.py` — all Pydantic models + validators | `models.py` |
| 4 | Build `middleware/auth.py` + `middleware/sanitize.py` | `auth.py`, `sanitize.py` |
| 5 | Build `job_manager.py` — queue, submit, cancel, dequeue, timeout, scraper integration | `job_manager.py` |

### Week 2

| Day | Tasks | Files |
|-----|-------|-------|
| 6 | Build `routes/users.py` + `routes/health.py` | `users.py`, `health.py` |
| 7 | Build `routes/jobs.py` (core: submit, list, detail, cancel, results) | `jobs.py` |
| 8 | Build `app.py` + `server.py` + update `config.py` | `app.py`, `server.py`, `config.py` |
| 9 | Write all tests from WS-1.13, fix failures | `tests/test_*.py` x 8 |
| 10 | Integration test: full lifecycle, fix edge cases, ensure `ruff check` + `pytest` pass | — |

---

## Dependencies Between Workstreams

```
WS-1.1 (deps, scaffold)
  ├─→ WS-1.2 (store.py)
  │     ├─→ WS-1.4 (auth middleware)
  │     ├─→ WS-1.5 (sanitize middleware)
  │     ├─→ WS-1.6 (job_manager.py)
  │     └─→ WS-1.7-9 (routes)
  │           └─→ WS-1.10 (app.py)
  │                 └─→ WS-1.11 (server.py)
  │
  └─→ WS-1.3 (models.py)
        ├─→ WS-1.5 (sanitize)
        ├─→ WS-1.6 (job_manager.py)
        └─→ WS-1.7-9 (routes)
```

WS-1.12 (config.py) and WS-1.13 (tests) run in parallel with respective dependencies.

---

## Success Criteria Checklist

- [ ] `POST /api/v1/jobs` with `{keyword, location, target}` returns `job_id` + status
- [ ] Duplicate detection: same `keyword+location` for same user with `queued`/`running` status returns `DUPLICATE_JOB`
- [ ] Queue auto-advances when a job finishes (FIFO order)
- [ ] `GET /api/v1/jobs/{id}/results?format=json` returns scraped leads
- [ ] `GET /api/v1/jobs/{id}/results?format=csv` exports CSV
- [ ] `GET /api/v1/jobs/{id}` includes `queue_position` and `estimated_wait_minutes`
- [ ] API key auth blocks unauthorized access (401 on missing/invalid key)
- [ ] Admin-only endpoints (user CRUD) return 403 for non-admin users
- [ ] Job timeout: running job >30min auto-cancels, partial results saved
- [ ] Graceful shutdown: SIGTERM marks running job as failed, closes DB cleanly
- [ ] Startup recovery: orphan `running` jobs marked `failed`, queue rebuilt
- [ ] `GET /api/v1/health` returns 200 when DB is connected
- [ ] `GET /api/v1/system` reports RAM, CPU, disk, active/queued job counts
- [ ] All 8 test files pass (ruff + pytest, 100% pass rate)
- [ ] Input sanitization: blocked chars rejected, SQL injection patterns stripped

---

## Out of Scope for Phase 1

| Item | Phase |
|------|-------|
| Job listing with pagination + filters | P2 |
| Queue admin management (reorder/remove) | P2 |
| Results query engine (filters, search, dedup view) | P2 |
| Audit log endpoint | P2 |
| Data retention auto-cleanup | P2 |
| Rate limiting | P2 |
| SSE streaming | P3 |
| Config management API | P3 |
| Webhook notifications | P3 |
| CORS configuration | P3 |
| Structured JSON logging | P3 |
| systemd service file | P3 |
| Integration tests | P3 |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Camoufox crash blocks queue | Job timeout (30 min), auto-cancel + dequeue next |
| Server restart loses queue | Startup recovery reconstructs from SQLite |
| SQLite write contention | WAL mode, batched writes per scraping batch |
| Duplicate job floods queue | Reject if same keyword+location+user with queued/running status |

*Source: [`docs/blueprint-backend-api.md`](../../blueprint-backend-api.md), [`docs/PRD-backend-api.md`](../../PRD-backend-api.md)*
