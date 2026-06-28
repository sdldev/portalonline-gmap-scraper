# Phase 3: Real-time, Webhooks & Production (Week 4)

**Goal**: Polish for production deployment with real-time feedback, integration hooks, and systemd reliability.

**Success Gate**: SSE streams progress <2s latency; webhook fires on job complete; systemd auto-restart works; config changes via API take effect.

**Prerequisites**: Phase 1 + Phase 2 complete.

---

## Workstreams & Tasks

### WS-3.1: SSE Streaming (`sse.py` + `routes/jobs.py` extend)

| Task | Description |
|------|-------------|
| `SEEmitter` class | Manages SSE connections per job. `subscribe(job_id)` → returns `AsyncGenerator[str, None]` |
| Event types | `progress` (leads_collected, total), `status_change` (old→new status), `error` (message), `heartbeat` (every 15s), `completed` (final summary) |
| `GET /api/v1/jobs/{job_id}/stream` | SSE endpoint. Content-Type: `text/event-stream`. Keep-alive via heartbeat. |
| Connection lifecycle | Subscribe on connect, unsubscribe on disconnect. Clean up stale connections. Max 100 concurrent SSE connections. |
| JobManager hooks | JobManager calls `emitter.broadcast(job_id, event)` on progress update, status change, completion |
| Headers | `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no` |
| Tests | In `tests/test_routes_jobs.py` — SSE events received, heartbeat, disconnect cleanup |

**SSE event format**:
```
event: progress
data: {"job_id": "...", "leads_collected": 15, "total": 50, "timestamp": "..."}

event: status_change
data: {"job_id": "...", "old_status": "queued", "new_status": "running", "timestamp": "..."}

event: heartbeat
data: {"timestamp": "..."}

event: completed
data: {"job_id": "...", "leads_collected": 50, "status": "completed", "timestamp": "..."}
```

### WS-3.2: Config Management API (`routes/config.py`)

| Task | Description |
|------|-------------|
| `GET /api/v1/config` | Admin only. Return all runtime config values (exclude secrets like API keys). |
| `PATCH /api/v1/config` | Admin only. Partial update. Body: `{batch_size: 10, cooldown_sec: 5}`. Validated by Pydantic. Changes take effect on next job (no server restart). |
| `ConfigUpdate` model | All fields optional: `batch_size`, `cooldown_sec`, `mem_limit_mb`, `cpu_limit_percent`, `max_retries`, `headless`, `max_job_duration_minutes`, `disk_usage_warn_percent`, `disk_usage_limit_percent` |
| Audit | Log config changes to audit_logs with old/new values diff |
| Tests | In `tests/test_routes_admin.py` — view config, update config, invalid values rejected, RBAC enforcement |

### WS-3.3: Webhook Notifications (`webhook.py`)

| Task | Description |
|------|-------------|
| `WebhookService` | Manages webhook delivery. Called by JobManager on job.completed/job.failed. |
| User endpoints | `POST /api/v1/users/me/webhook` (set URL + events), `GET` (view), `DELETE` (remove) |
| Webhook payload | `{event, timestamp, job_id, keyword, location, leads_collected, status}` |
| Delivery | Retry 3x with exponential backoff (1s, 5s, 30s). Timeout 10s per attempt. Log delivery status to audit_logs. Non-blocking (fire-and-forget). |
| `WebhookConfig` model | `url: str` (max 500), `events: list[str]` (default: ["job.completed", "job.failed"]) |
| Error handling | Failed delivery logged as warning. Doesn't block job completion. Max 3 retries then give up. |
| Tests | `tests/test_webhook.py` — set/get/delete webhook, payload format, retry logic (mocked HTTP), failed delivery log |

### WS-3.4: CORS Configuration (`app.py` — enhance)

| Task | Description |
|------|-------------|
| `CORS_ORIGINS` env var | Comma-separated list of allowed origins. Default: `*` (dev), tighten for production |
| `CORSMiddleware` | FastAPI built-in. Allow origins, methods, headers from config. |
| Documentation | Comment in `.env` example: production should set specific frontend domain |

### WS-3.5: Structured JSON Logging (`config.py` + `server.py`)

| Task | Description |
|------|-------------|
| Log format | JSON-structured logs to stdout: `{timestamp, level, logger, message, request_id?, user_id?, job_id?}` |
| Log rotation | Via systemd journal (no in-app rotation). stdout/stderr captured by journald. |
| Log levels | DEBUG (dev), INFO (prod default), WARNING, ERROR. Configurable via `LOG_LEVEL` env var. |
| Request logging | Middleware logs every request: method, path, status, duration_ms, user_id |
| Implementation | Use Python `logging` with JSON formatter. No external dependency needed. |

### WS-3.6: systemd Service File (`deploy/portalonline-scraper.service`)

| Task | Description |
|------|-------------|
| Service file | `deploy/portalonline-scraper.service` |
| Configuration | User=indatech, WorkingDirectory=/home/indatech/Documents/BOT/portalonline-gmap-scraper, ExecStart=venv/bin/python -m portalonline_gmap_scraper.server |
| Auto-restart | `Restart=on-failure`, `RestartSec=10` |
| After | `After=network.target` |
| Environment | Load from `.env` file via `EnvironmentFile` |
| Logging | stdout/stderr captured by journald. View with `journalctl -u portalonline-scraper -f` |
| Install instructions | Documented in service file comments: `sudo cp deploy/portalonline-scraper.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now portalonline-scraper` |

### WS-3.7: Integration Tests

| Task | Description |
|------|-------------|
| Full lifecycle test | create user → submit job → queue → scrape → results → webhook → cleanup |
| Setup | Real SQLite (in-memory or temp file), mocked scraper, TestClient |
| Scenarios | Job completes normally, job fails (simulated error), job timeout, duplicate detection, queue ordering, admin reorder/cancel |
| Webhook test | Mock HTTP server receives webhook POST on job complete |
| SSE test | SSE stream receives progress events during simulated scrape |
| Test file | `tests/test_startup_recovery.py` — startup recovery, graceful shutdown, orphan job marking |

### WS-3.8: Startup Recovery Hardening (`server.py` — enhance)

| Task | Description |
|------|-------------|
| Orphan job handling | On startup: mark all `status=running` jobs as `failed` with `error="Server restarted"` |
| Queue reconstruction | Rebuild in-memory queue from `status=queued` jobs ORDER BY `queue_position ASC` |
| Default admin | If no users exist, create admin from `ADMIN_API_KEY` env var. If env var missing, generate random key + log prominently. |
| DB health check | Verify SQLite file exists, tables present, WAL mode enabled. Log warning if issues. |

---

## Implementation Order (Day-by-Day)

### Week 4

| Day | Tasks | Files |
|-----|-------|-------|
| 1 | Build `sse.py` — SSE emitter, subscribe/unsubscribe, event types | `sse.py` |
| 2 | Integrate SSE into JobManager + `routes/jobs.py` (stream endpoint) | `job_manager.py` (extend), `routes/jobs.py` (extend) |
| 3 | Build `routes/config.py` — GET/PATCH config, audit config changes | `routes/config.py` |
| 4 | Build `webhook.py` — webhook service, user endpoints, retry logic | `webhook.py`, `routes/users.py` (extend) |
| 5 | CORS config + structured JSON logging | `app.py` (extend), `config.py` (extend) |
| 6 | Create systemd service file + deploy instructions | `deploy/portalonline-scraper.service` |
| 7 | Write all Phase 3 tests + integration tests | `tests/test_webhook.py`, `tests/test_startup_recovery.py`, extend existing |
| 8 | Final integration test: full lifecycle, `ruff check` + `pytest` 100%, production readiness review | — |

---

## Dependencies Between Workstreams

```
WS-3.1 (SSE) — depends on WS-1.6 (JobManager progress tracking)
WS-3.2 (config API) — depends on WS-1.12 (config.py)
WS-3.3 (webhook) — depends on WS-1.6 (JobManager completion hooks)
WS-3.4 (CORS) — extends WS-1.10 (app.py)
WS-3.5 (logging) — extends WS-1.12 (config.py)
WS-3.6 (systemd) — depends on WS-1.11 (server.py) — independent otherwise
WS-3.7 (integration tests) — depends on everything
WS-3.8 (startup recovery hardening) — extends WS-1.11 (server.py)
```

WS-3.1 through WS-3.6 can be built in parallel (different files, minimal overlap).

---

## Success Criteria Checklist

- [ ] SSE stream delivers `progress` events with <2s latency during scraping
- [ ] SSE sends `heartbeat` every 15s to keep connection alive
- [ ] SSE sends `status_change` on queued→running, running→completed/failed/cancelled
- [ ] Multiple SSE connections for same job all receive events
- [ ] `GET /api/v1/config` returns all runtime settings (admin only)
- [ ] `PATCH /api/v1/config` updates config, changes take effect on next job
- [ ] Config changes logged to audit_logs with old/new diff
- [ ] `POST /api/v1/users/me/webhook` saves webhook URL + events
- [ ] Webhook fires on `job.completed` and `job.failed` with correct payload
- [ ] Webhook retries 3x with exponential backoff on failure
- [ ] Failed webhook delivery doesn't block job completion
- [ ] CORS origins configurable via `CORS_ORIGINS` env var
- [ ] JSON-structured logs contain timestamp, level, logger, message
- [ ] systemd service file: `systemctl start portalonline-scraper` works
- [ ] systemd auto-restart on crash: `Restart=on-failure`
- [ ] Startup recovery: orphan running jobs marked failed, queue rebuilt
- [ ] Graceful shutdown: active job cancelled, DB closed, SSE connections cleaned
- [ ] Integration test: full lifecycle passes (create user → submit → queue → scrape → results → webhook)
- [ ] All Phase 3 tests pass (ruff + pytest, 100%)

---

## Out of Scope for v1

| Item | Notes |
|------|-------|
| Scheduled/cron scraping | Nice-to-Have #10 from PRD |
| Google Sheets export | Nice-to-Have #11 from PRD |
| Web frontend (keyword input form) | Nice-to-Have #12, separate project |
| Multi-VPS horizontal scaling | Redis/PostgreSQL distributed queue |
| OAuth2/SSO | Enterprise identity provider |
| Category variations CRUD API | Manage keyword variants via API |

---

## Production Deployment Checklist

- [ ] `.env` configured with production values (ADMIN_API_KEY, CORS_ORIGINS, LOG_LEVEL=INFO)
- [ ] systemd service installed and enabled
- [ ] UptimeRobot or similar monitoring pinging `GET /api/v1/health` every 60s
- [ ] Disk space >20% free, verified via `GET /api/v1/system`
- [ ] Logs flowing to journald: `journalctl -u portalonline-scraper -f`
- [ ] Camoufox browser working correctly in headless mode
- [ ] Firewall: port 9988 accessible (if remote access needed) or nginx reverse proxy
- [ ] Backup strategy for `data/scraper.db` (cron rsync or similar)

*Source: [`docs/blueprint-backend-api.md`](../../blueprint-backend-api.md), [`docs/PRD-backend-api.md`](../../PRD-backend-api.md)*
