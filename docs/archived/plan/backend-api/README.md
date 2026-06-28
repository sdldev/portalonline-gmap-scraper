# Backend REST API — Implementation Plans

**Source**: [`docs/blueprint-backend-api.md`](../../blueprint-backend-api.md)
**PRD**: [`docs/PRD-backend-api.md`](../../PRD-backend-api.md)
**Status**: Planning

---

## Overview

Transformasi PortalOnline GMap Scraper dari CLI-only tool menjadi **self-service scraping platform** via HTTP API (port 9988). Tiga phase, 4 minggu total.

| Phase | Duration | Focus | Plan Doc |
|-------|----------|-------|----------|
| Phase 1 | Week 1-2 | MVP: Walking skeleton (submit job, queue, results, auth) | [`phase-1-mvp-core-platform.md`](phase-1-mvp-core-platform.md) |
| Phase 2 | Week 3 | Monitoring, audit, cleanup, admin tooling | [`phase-2-monitoring-audit-cleanup.md`](phase-2-monitoring-audit-cleanup.md) |
| Phase 3 | Week 4 | Real-time SSE, webhooks, production hardening | [`phase-3-realtime-webhooks-production.md`](phase-3-realtime-webhooks-production.md) |

## Architecture Summary

```
Uvicorn (port 9988)
  └─ FastAPI App
       ├─ Middleware: Auth (API Key + RBAC), Rate Limit, Sanitize
       ├─ Routes: users, jobs, queue, results, config, health, admin
       ├─ JobManager: FIFO queue, single-worker (Camoufox limit), timeout
       ├─ SQLiteStore: users, jobs, leads, audit_logs (WAL mode)
       ├─ SSE: real-time progress streaming
       ├─ Webhook: job completion notifications
       └─ Cleanup: auto-retention (90 days), manual cleanup endpoint
```

**Key constraints**:
- Single worker only (Camoufox crashes with >1 concurrent page)
- Total footprint <2GB RAM (browser ~900MB + server ~100MB + SQLite)
- VPS deployment via systemd on Ubuntu/Debian

## File Inventory

### New files (24 total)

| # | File | Phase | Purpose |
|---|------|-------|---------|
| 1 | `portalonline_gmap_scraper/api/__init__.py` | P1 | Package init |
| 2 | `portalonline_gmap_scraper/api/app.py` | P1 | FastAPI app factory |
| 3 | `portalonline_gmap_scraper/api/models.py` | P1 | Pydantic request/response models |
| 4 | `portalonline_gmap_scraper/api/store.py` | P1 | SQLite persistence layer |
| 5 | `portalonline_gmap_scraper/api/job_manager.py` | P1 | Job queue & lifecycle |
| 6 | `portalonline_gmap_scraper/api/sse.py` | P3 | SSE streaming helper |
| 7 | `portalonline_gmap_scraper/api/webhook.py` | P3 | Webhook delivery service |
| 8 | `portalonline_gmap_scraper/api/cleanup.py` | P2 | Data retention scheduler |
| 9 | `portalonline_gmap_scraper/api/routes/__init__.py` | P1 | Routes package |
| 10 | `portalonline_gmap_scraper/api/routes/users.py` | P1 | User management (admin) |
| 11 | `portalonline_gmap_scraper/api/routes/jobs.py` | P1 | Job CRUD + results |
| 12 | `portalonline_gmap_scraper/api/routes/queue.py` | P2 | Queue management |
| 13 | `portalonline_gmap_scraper/api/routes/results.py` | P2 | Results query/export |
| 14 | `portalonline_gmap_scraper/api/routes/config.py` | P3 | Config endpoints |
| 15 | `portalonline_gmap_scraper/api/routes/health.py` | P1 | Health + system endpoints |
| 16 | `portalonline_gmap_scraper/api/routes/admin.py` | P2 | Admin endpoints (audit, cleanup, db-stats) |
| 17 | `portalonline_gmap_scraper/api/middleware/__init__.py` | P1 | Middleware package |
| 18 | `portalonline_gmap_scraper/api/middleware/auth.py` | P1 | API key + RBAC |
| 19 | `portalonline_gmap_scraper/api/middleware/rate_limit.py` | P2 | Per-user rate limiter |
| 20 | `portalonline_gmap_scraper/api/middleware/sanitize.py` | P1 | Input sanitization |
| 21 | `portalonline_gmap_scraper/server.py` | P1 | Uvicorn entry point |
| 22 | `deploy/portalonline-scraper.service` | P3 | systemd service file |
| 23 | `data/` (directory, gitignored) | P1 | SQLite DB location |

### Modified files (4 total)

| # | File | Phase | Changes |
|---|------|-------|---------|
| 1 | `pyproject.toml` | P1 | Add fastapi, uvicorn, pydantic, aiosqlite, httpx |
| 2 | `portalonline_gmap_scraper/__init__.py` | P1 | Export API module |
| 3 | `portalonline_gmap_scraper/config.py` | P1 | Add API config vars |
| 4 | `.gitignore` | P1 | Add `data/` directory |

### Test files (14 total)

| # | File | Phase | Purpose |
|---|------|-------|---------|
| 1 | `tests/test_api_models.py` | P1 | Pydantic model validation |
| 2 | `tests/test_store.py` | P1 | SQLite CRUD |
| 3 | `tests/test_job_manager.py` | P1 | Job lifecycle + queue |
| 4 | `tests/test_routes_users.py` | P1 | User endpoints + RBAC |
| 5 | `tests/test_routes_jobs.py` | P1 | Job endpoints + user isolation |
| 6 | `tests/test_routes_health.py` | P1 | Health endpoint |
| 7 | `tests/test_auth.py` | P1 | Auth middleware |
| 8 | `tests/test_sanitize.py` | P1 | Input sanitization |
| 9 | `tests/test_routes_results.py` | P2 | Results query/export |
| 10 | `tests/test_routes_queue.py` | P2 | Queue management |
| 11 | `tests/test_routes_admin.py` | P2 | Admin endpoints |
| 12 | `tests/test_rate_limit.py` | P2 | Rate limiter |
| 13 | `tests/test_webhook.py` | P3 | Webhook delivery |
| 14 | `tests/test_startup_recovery.py` | P3 | Startup/shutdown |

## Implementation Order (Critical Path)

```
Phase 1:
  deps → store.py → models.py → middleware/auth.py → middleware/sanitize.py
  → job_manager.py → routes/* → app.py → server.py → tests

Phase 2:
  middleware/rate_limit.py → cleanup.py → routes/results.py → routes/queue.py
  → routes/admin.py → tests

Phase 3:
  sse.py → webhook.py → routes/config.py → server.py (systemd) → tests
```

## Success Gates Per Phase

| Phase | Gate |
|-------|------|
| P1 | `POST /api/v1/jobs` → queue → scrape → `GET /api/v1/jobs/{id}/results` works end-to-end |
| P2 | Admin can view all jobs, reorder queue, run cleanup; audit log traces all actions |
| P3 | SSE streams progress <2s latency; webhook fires on job complete; systemd auto-restart works |

## References

- [Blueprint (strategy)](../../blueprint-backend-api.md)
- [PRD (detailed specs)](../../PRD-backend-api.md)
- [ROADMAP](../../ROADMAP.md)
- [AGENTS.md](../../../AGENTS.md) — coding conventions, test patterns, ruff config
