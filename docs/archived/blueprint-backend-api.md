# Product Blueprint: Backend REST API for PortalOnline GMap Scraper

**Status**: Draft — derived from `docs/PRD-backend-api.md`
**Date**: 2025-06-29
**Audience**: Engineering, Product, Operations

---

## 1. Executive Summary

### Vision

Transform PortalOnline GMap Scraper from a CLI-only tool with CSV output into a **self-service scraping platform** accessible via HTTP API. End users can trigger scrapes, monitor progress in real time, and query structured results, all without needing VPS access or technical knowledge of the scraper internals. Administrators get full queue management, user provisioning, and system health visibility.

### Value Proposition

| Before (CLI-only) | After (API Platform) |
|---|---|
| SSH into VPS required | HTTP call from anywhere |
| CSV files, easy to overwrite | SQLite persistence, indexed, queryable |
| No progress visibility | Real-time SSE streaming |
| No job history or cancellation | Full lifecycle management + queue |
| Single-user only | Multi-user with RBAC (admin/user roles) |
| No integration surface | Frontend, bots, dashboards can consume API |

### One-line Summary

A lightweight (<2GB total footprint) FastAPI service on port 9988 that wraps the existing Camoufox scraper with SQLite persistence, a FIFO job queue, role-based access control, and real-time progress streaming.

---

## 2. Strategic Context

### Why Now

The scraper's CLI-only interface limits adoption. Internal stakeholders (operations team, business development) need to request lead lists without involving engineering for every run. A REST API unlocks:

- **Self-service**: Non-technical users trigger scrapes via a future web UI or bot commands.
- **Integration**: Results feed into dashboards, CRM pipelines, and reporting tools.
- **Observability**: Job history and audit trails enable accountability and debugging.
- **Scale**: Multi-user support with queue fairness means the VPS can serve multiple departments.

### Business Goals

1. Reduce engineering time spent on ad-hoc scraping requests by 90%.
2. Provide a permanent, searchable lead database (replacing transient CSV files).
3. Enable autonomous scraping scheduled by operations teams.

### Constraints

- **Single worker only**: Camoufox (Firefox) crashes with >1 concurrent browser page. Queue model is mandatory, not optional.
- **RAM budget <2GB total**: Browser (~900MB) + API server (~100MB idle) + SQLite. Must fit within VPS's 5GB.
- **VPS-only deployment**: No Kubernetes, no Docker Swarm. Systemd service on Ubuntu/Debian VPS.

### Target Users

| Persona | Role | Needs |
|---|---|---|
| Operator (end-user) | `user` | Submit job, view own progress/results, cancel own jobs |
| System Admin | `admin` | Manage all jobs, users, queue, config; monitor system health |
| Frontend App | machine | Consume API endpoints, render UI |

---

## 3. Key Workstreams

### Phase 1: MVP — Core Platform (Week 1-2)

**Goal**: Ship a minimal but complete platform that can accept scraping jobs via API, persist results to SQLite, and provide basic job visibility. This is the "walking skeleton" that proves the architecture.

**Deliverables**:

| # | Workstream | Owner | Key Output |
|---|---|---|---|
| WS-1.1 | FastAPI app skeleton | Backend | `server.py`, `app.py`, dependency wiring |
| WS-1.2 | SQLite persistence layer | Backend | `store.py` with users, jobs, leads, audit_logs tables |
| WS-1.3 | User management + RBAC middleware | Backend | `auth.py`, admin-only CRUD endpoints |
| WS-1.4 | Job submission + FIFO queue | Backend | `job_manager.py`, duplicate detection, auto-dequeue |
| WS-1.5 | Scraper integration | Backend | Wire `scrape()/scrape_smart()` to JobManager, batch-write leads to DB |
| WS-1.6 | Results retrieval | Backend | JSON/CSV export from SQLite with user isolation |
| WS-1.7 | Health check endpoint | Backend | `GET /api/health` |
| WS-1.8 | Startup recovery + graceful shutdown | Backend | Reconstruct queue from DB, mark orphan jobs failed |
| WS-1.9 | Unit tests | Backend | `test_store.py`, `test_job_manager.py`, `test_routes_*.py` |

**Success Criteria**:
- `POST /api/v1/jobs` accepts keyword/location/target and returns job_id.
- Queue auto-advances when a job finishes.
- Results retrievable via `GET /api/v1/jobs/{id}/results?format=json`.
- API key authentication blocks unauthorized access.
- All tests pass (`ruff check` + `pytest`).

### Phase 2: Monitoring, Audit & Cleanup (Week 3)

**Goal**: Add operational visibility, data hygiene, and admin tooling to make the platform production-safe.

**Deliverables**:

| # | Workstream | Owner | Key Output |
|---|---|---|---|
| WS-2.1 | Job listing + pagination | Backend | `GET /api/v1/jobs` with filters (status, keyword, user_id) |
| WS-2.2 | Job cancellation with RBAC | Backend | `DELETE /api/v1/jobs/{id}`, user cancels own, admin cancels any |
| WS-2.3 | Queue management (admin) | Backend | `PATCH/DELETE /api/v1/queue/{job_id}` for reorder/remove |
| WS-2.4 | System monitoring | Backend | `GET /api/v1/system` (RAM, CPU, disk, active jobs) |
| WS-2.5 | Results query engine | Backend | Filter-rich `GET /api/v1/results` (keyword, phone, rating, search, dedup view) |
| WS-2.6 | Audit logging | Backend | All create/cancel/config actions logged to `audit_logs` table |
| WS-2.7 | Data retention + cleanup | Backend | Auto-cleanup jobs/leads >90 days, manual `POST /api/v1/admin/cleanup` |
| WS-2.8 | Rate limiting | Backend | 60 req/min per user, admin exempt |
| WS-2.9 | Admin dashboard data | Backend | `GET /api/v1/admin/db-stats`, `GET /api/v1/admin/audit-logs` |

**Success Criteria**:
- Admin can view/delete any job and reorder the queue from API.
- Disk space guard rejects new jobs when disk >90%.
- Auto-cleanup runs daily at 03:00, reclaiming space via VACUUM.
- All significant actions traceable via audit log endpoint.

### Phase 3: Real-time, Webhooks & Production (Week 4)

**Goal**: Polish for production deployment with real-time feedback and integration hooks.

**Deliverables**:

| # | Workstream | Owner | Key Output |
|---|---|---|---|
| WS-3.1 | SSE streaming | Backend | `GET /api/v1/jobs/{id}/stream` with progress/status_change/heartbeat events |
| WS-3.2 | Config management API | Backend | `GET/PATCH /api/v1/config` (admin-only runtime config changes) |
| WS-3.3 | Webhook notifications | Backend | User configures webhook URL, receives POST on job.completed/job.failed |
| WS-3.4 | Input sanitization hardening | Backend | Pydantic validators for keyword, location, username, api_key fields |
| WS-3.5 | CORS configuration | Backend | Configurable `CORS_ORIGINS` for frontend integration |
| WS-3.6 | Structured JSON logging | Backend | Log rotation, machine-parseable format for log aggregators |
| WS-3.7 | Systemd service file | DevOps | `deploy/portalonline-scraper.service` with auto-restart |
| WS-3.8 | Integration tests | QA | Full lifecycle: create user -> submit job -> queue -> scrape -> results -> webhook |

**Success Criteria**:
- SSE stream delivers progress updates with <2s latency.
- Webhook fires on job completion with 3x retry on failure.
- Server starts reliably via `systemctl start portalonline-scraper`.
- Config changes via API take effect on next job without server restart.

---

## 4. Operational Readiness

### Deployment Model

- **Infrastructure**: Single VPS (4 CPU / 5GB RAM) running Ubuntu/Debian.
- **Process**: Single Uvicorn process on port 9988, managed by systemd.
- **Database**: SQLite file at `data/scraper.db` with WAL mode enabled.
- **Startup**: `systemctl enable portalonline-scraper` for boot-time auto-start.

### Monitoring & Alerting

| What | How | Alert Threshold |
|---|---|---|
| Uptime | `GET /api/health` pinged by UptimeRobot every 60s | 3 consecutive failures |
| RAM usage | `GET /api/system` reports `ram_available_mb` | < 500MB available |
| Disk usage | `GET /api/system` reports `disk_usage_percent` | > 80% warning, > 90% reject jobs |
| Failed jobs | `GET /api/jobs?status=failed` | > 5 failed in last hour |
| Queue depth | `GET /api/queue` reports `total_queued` | > 10 queued jobs |

### Support & Feedback Loops

- **Admin dashboard** (future frontend work): Builds on Phase 2 admin endpoints.
- **Audit trail**: `GET /api/v1/admin/audit-logs` answers "who did what and when".
- **Webhook integration**: Operations team can pipe job results into Slack/Telegram.
- **Log aggregation**: JSON-structured stdout logs can be consumed by Loki, Datadog, or plain `journalctl`.

### Risk Register (Top 5)

| # | Risk | Severity | Mitigation | Owner |
|---|---|---|---|---|
| R1 | Camoufox crash blocks queue indefinitely | High | Job timeout (30 min), auto-cancel + dequeue next | Backend |
| R2 | Disk fills from accumulated leads | Medium | Disk space guard (reject >90%), auto-cleanup 90-day retention, VACUUM | Backend |
| R3 | Server restart loses queue state | Medium | Startup recovery reconstructs queue from SQLite, marks orphans failed | Backend |
| R4 | User submits duplicate jobs, floods queue | Medium | Duplicate detection (same keyword+location+user, queued/running), reject | Backend |
| R5 | SQLite write contention | Low | WAL mode (readers don't block), writes batched per scraping batch | Backend |

### Key Decisions

| Decision | Rationale |
|---|---|
| SQLite over PostgreSQL | Zero-config, file-based, fits VPS constraint. WAL mode handles concurrent reads. No separate DB server process needed. |
| FastAPI over Flask | Native async, built-in SSE, auto OpenAPI docs, Pydantic validation. Scraper is already async. |
| API key over JWT/OAuth | Simplest auth for machine-to-machine API. No token refresh, no OAuth provider dependency. Future upgrade path remains open. |
| SSE over WebSocket | Unidirectional server->client streaming is sufficient. SSE is simpler, auto-reconnects, works through proxies. |
| Single worker (no horizontal scaling) | Camoufox limitation (crashes with >1 concurrent page). Queue model sidesteps this cleanly. Multi-VPS scaling is a future concern. |

### Future Horizons (Out of Scope for v1)

- **Scheduled/cron scraping** (Nice-to-Have #10 from PRD).
- **Google Sheets export** (Nice-to-Have #11 from PRD).
- **Web frontend** for keyword input form (Nice-to-Have #12 from PRD, separate project).
- **Multi-VPS horizontal scaling** with distributed queue (PostgreSQL or Redis).
- **OAuth2/SSO** authentication for enterprise integration.
- **Category variations CRUD API** to let operators manage search keywords.

---

## Appendix: API Surface Summary

```
POST   /api/v1/users                  # Create user (admin)
GET    /api/v1/users                  # List users (admin)
GET    /api/v1/users/me               # View own profile
GET    /api/v1/users/{user_id}        # Get user detail (admin)
PATCH  /api/v1/users/{user_id}        # Update user (admin)
DELETE /api/v1/users/{user_id}        # Delete user (admin)

POST   /api/v1/jobs                   # Submit scraping job
GET    /api/v1/jobs                   # List jobs (own for user, all for admin)
GET    /api/v1/jobs/{job_id}          # Job detail + queue_position
DELETE /api/v1/jobs/{job_id}          # Cancel job (RBAC)
GET    /api/v1/jobs/{job_id}/results  # Get results (JSON/CSV)
GET    /api/v1/jobs/{job_id}/stream   # SSE progress stream

GET    /api/v1/queue                  # Queue status
PATCH  /api/v1/queue/{job_id}         # Reorder queue (admin)
DELETE /api/v1/queue/{job_id}         # Remove from queue (admin)

GET    /api/v1/results                # List all results with filters
GET    /api/v1/results/{result_id}    # Single lead detail
GET    /api/v1/results/stats          # Aggregate statistics
GET    /api/v1/results/export         # Export (CSV/JSON)
GET    /api/v1/results/search         # Full-text search

GET    /api/v1/config                 # View config (admin)
PATCH  /api/v1/config                 # Update config (admin)

GET    /api/v1/health                 # Health check (200/503)
GET    /api/v1/system                 # Resource monitoring

POST   /api/v1/users/me/webhook       # Set webhook URL
GET    /api/v1/users/me/webhook       # View webhook config
DELETE /api/v1/users/me/webhook       # Remove webhook

GET    /api/v1/admin/audit-logs       # Audit trail (admin)
POST   /api/v1/admin/cleanup          # Manual data cleanup (admin)
GET    /api/v1/admin/db-stats         # Database stats (admin)
```

---

*Blueprint derived from `docs/PRD-backend-api.md`. For detailed technical specifications, data models, and SQL schemas, refer to the PRD.*
