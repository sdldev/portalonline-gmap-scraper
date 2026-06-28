# Phase 2: Monitoring, Audit & Cleanup (Week 3)

**Goal**: Add operational visibility, data hygiene, and admin tooling to make the platform production-safe.

**Success Gate**: Admin can view all jobs, reorder queue, run cleanup; audit log traces all significant actions.

**Prerequisites**: Phase 1 complete (walking skeleton functional).

---

## Workstreams & Tasks

### WS-2.1: Rate Limiter (`middleware/rate_limit.py`)

| Task | Description |
|------|-------------|
| `RateLimiter` class | Per-user rate tracking: 60 requests/minute. Admin exempt. |
| Storage | In-memory dict: `{user_id: deque[timestamp]}`. Clean stale entries periodically. |
| `check_rate()` | Dependency: extract user_id, count requests in last 60s window, raise 429 if exceeded |
| Response headers | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After` on 429 |
| Tests | `tests/test_rate_limit.py` — under limit, at limit, admin exempt, window roll-off |

### WS-2.2: Data Retention & Cleanup (`cleanup.py`)

| Task | Description |
|------|-------------|
| `CleanupScheduler` | Background asyncio task: run daily at 03:00, delete jobs+leads > `DATA_RETENTION_DAYS` (default 90) |
| `run_cleanup()` | Delete old completed/failed/cancelled jobs (CASCADE deletes leads). Delete old audit_logs. Run `PRAGMA incremental_vacuum`. Return stats. |
| `POST /api/v1/admin/cleanup` | Manual trigger (admin only). Body: `{older_than_days: 30}` optional. Response: `{deleted_jobs, deleted_leads, deleted_audit_logs, db_size_before_mb, db_size_after_mb}` |
| `GET /api/v1/admin/db-stats` | Database statistics: size, row counts per table, last vacuum time |
| Config vars | `DATA_RETENTION_DAYS` (default 90), `AUTO_CLEANUP_HOUR` (default 3) |
| Tests | In `tests/test_routes_admin.py` — cleanup endpoint, db-stats endpoint |

### WS-2.3: Job Listing Enhancement (`routes/jobs.py` — extend)

| Task | Description |
|------|-------------|
| Pagination | `GET /api/v1/jobs?page=1&limit=20` — default page=1, limit=20, max limit=100 |
| Filters | Query params: `status`, `keyword`, `user_id` (admin only) |
| Response format | `{jobs: [...], total, page, limit, pages}` |
| Sorting | Default: `created_at DESC`. Optional: `sort_by=created_at|status|leads_collected`, `order=desc|asc` |
| Tests | Extend `tests/test_routes_jobs.py` — pagination, filters, user isolation, admin filter by user_id |

### WS-2.4: Job Cancellation RBAC (`routes/jobs.py` — extend)

| Task | Description |
|------|-------------|
| `DELETE /api/v1/jobs/{job_id}` | User: cancel own queued/running jobs only. Admin: cancel any job from any user. |
| Cancel queued | Remove from queue, reindex positions, set status=cancelled |
| Cancel running | Signal JobManager to stop scraper, save partial leads, dequeue next, set status=cancelled |
| Audit log | Log cancel action: user_id, target_type=job, target_id=job_id |
| Tests | Extend `tests/test_routes_jobs.py` — user cancel own queued, user cancel own running, admin cancel any, forbidden (user cancel other's) |

### WS-2.5: Queue Management — Admin (`routes/queue.py`)

| Task | Description |
|------|-------------|
| `GET /api/v1/queue` | Admin: full queue view (active_job + queued list). User: only own position/status. |
| `PATCH /api/v1/queue/{job_id}` | Admin: reorder queue position. Body: `{position: 1}`. Reindex remaining queue. |
| `DELETE /api/v1/queue/{job_id}` | Admin: remove from queue (cancel + remove). Soft-delete: set status=cancelled. |
| Response format | `{active_job: {job_id, user, keyword, started_at}, queue: [{job_id, user, keyword, position}, ...]}` |
| Tests | `tests/test_routes_queue.py` — admin list full queue, user see only own, reorder, remove, reindex after reorder |

### WS-2.6: Results Query Engine (`routes/results.py`)

| Task | Description |
|------|-------------|
| `GET /api/v1/results` | List leads with rich filters and pagination |
| Filters | `keyword`, `job_id`, `phone_not_null` (bool), `website_not_null` (bool), `rating_min` (float), `review_count_min` (int), `search` (text search in name+address) |
| Pagination | `page`, `limit` (default 50, max 500) |
| Dedup view | Query param `dedup=true`: hide duplicates (application-level check by name+address normalized) |
| `GET /api/v1/results/{result_id}` | Single lead detail by ID |
| `GET /api/v1/results/stats` | Aggregate stats: total_leads, unique_keywords, leads_with_phone, leads_with_website, leads_with_rating, avg_rating |
| `GET /api/v1/results/export` | Export CSV/JSON. Params: `format=csv|json`, `keyword`, `job_id` |
| `GET /api/v1/results/search` | Full-text search: `q` param searches name, address, phone |
| User isolation | All queries filtered by `user_id` unless admin (admin sees all) |
| Tests | `tests/test_routes_results.py` — filters, dedup, pagination, export, search |

### WS-2.7: Audit Log Endpoint (`routes/admin.py`)

| Task | Description |
|------|-------------|
| `GET /api/v1/admin/audit-logs` | List audit logs with filters (admin only) |
| Filters | `user_id`, `action`, `target_type`, `from_date`, `to_date` |
| Pagination | `page`, `limit` (default 50) |
| Response | `{logs: [...], total, page, limit}` |
| Audit actions | All create/cancel/config/queue/user actions logged automatically by middleware/service |

### WS-2.8: Disk Space Guard (`routes/health.py` — extend)

| Task | Description |
|------|-------------|
| Disk monitor | `GET /api/v1/system` reports `disk_usage_percent`, `disk_free_gb` |
| Job reject gate | `POST /api/v1/jobs` rejects with `DISK_SPACE_LOW` if disk > `DISK_USAGE_LIMIT_PERCENT` (default 90) |
| Warning | Health check warns if disk > `DISK_USAGE_WARN_PERCENT` (default 80) |
| Config vars | `DISK_USAGE_WARN_PERCENT`, `DISK_USAGE_LIMIT_PERCENT` |
| Tests | Extend `tests/test_routes_jobs.py` — job reject when disk full |

### WS-2.9: Tests (4 files)

| Test File | Coverage |
|-----------|----------|
| `tests/test_routes_results.py` | Results CRUD, filters (phone_not_null, rating_min, keyword), pagination, dedup view, export CSV/JSON, search |
| `tests/test_routes_queue.py` | Admin full queue view, user own view, reorder, remove, reindex after reorder |
| `tests/test_routes_admin.py` | Audit logs (filters, pagination), cleanup endpoint, db-stats endpoint |
| `tests/test_rate_limit.py` | Under limit, at limit (429), admin exempt, window roll-off |

**Extend existing tests**:
- `tests/test_routes_jobs.py` — add pagination, filters, cancel RBAC, disk space gate
- `tests/test_routes_health.py` — extend system endpoint with disk space

---

## Implementation Order (Day-by-Day)

### Week 3

| Day | Tasks | Files |
|-----|-------|-------|
| 1 | Build rate limiter + integrate into middleware | `rate_limit.py` |
| 2 | Build cleanup scheduler + auto-cleanup + manual cleanup endpoint | `cleanup.py`, `routes/admin.py` |
| 3 | Enhance job listing (pagination, filters) + cancel RBAC | `routes/jobs.py` (extend) |
| 4 | Build queue management routes (admin reorder/remove) | `routes/queue.py` |
| 5 | Build results query engine (filters, search, dedup, export, stats) + audit log endpoint | `routes/results.py`, `routes/admin.py` |
| 6 | Add disk space guard to health + job submission | `routes/health.py` (extend), `routes/jobs.py` (extend) |
| 7 | Write all Phase 2 tests + extend existing tests | `tests/test_*.py` x 4 + extend 2 |
| 8 | Integration: admin flow (view all, reorder, cleanup), fix edge cases, `ruff check` + `pytest` | — |

---

## Dependencies Between Workstreams

```
WS-2.1 (rate limiter) — independent
WS-2.2 (cleanup) → WS-2.7 (cleanup endpoint in admin.py)
WS-2.3 (job listing) — extends WS-1.8 (routes/jobs.py)
WS-2.4 (cancel RBAC) — extends WS-1.8 + depends on WS-1.6 (job_manager)
WS-2.5 (queue mgmt) — depends on WS-1.6 (job_manager queue ops)
WS-2.6 (results engine) — depends on WS-1.2 (store.py lead queries)
WS-2.7 (audit logs) — depends on WS-1.2 (audit_logs table)
WS-2.8 (disk guard) — extends WS-1.9 (health routes)
WS-2.9 (tests) — depends on all above
```

---

## Success Criteria Checklist

- [ ] `GET /api/v1/jobs` supports pagination (`page`, `limit`) and filters (`status`, `keyword`, `user_id`)
- [ ] `DELETE /api/v1/jobs/{id}`: user cancels own, admin cancels any, forbidden for cross-user cancel
- [ ] `GET /api/v1/queue`: admin sees all queued jobs, user sees only own position
- [ ] `PATCH /api/v1/queue/{job_id}` (admin): reorder to new position, reindex correctly
- [ ] `DELETE /api/v1/queue/{job_id}` (admin): remove from queue, job status=cancelled
- [ ] `GET /api/v1/results` with filters: `phone_not_null`, `rating_min`, `keyword`, `search` all work
- [ ] `GET /api/v1/results?dedup=true` hides duplicate leads (same name+address)
- [ ] `GET /api/v1/results/stats` returns correct aggregates
- [ ] `GET /api/v1/results/export?format=csv` exports valid CSV
- [ ] `GET /api/v1/admin/audit-logs` returns filtered, paginated audit trail
- [ ] `POST /api/v1/admin/cleanup` deletes old data, runs VACUUM, returns stats
- [ ] `GET /api/v1/admin/db-stats` reports DB size, row counts, last vacuum
- [ ] `POST /api/v1/jobs` rejects when disk > 90% with `DISK_SPACE_LOW` error
- [ ] Rate limiter: 429 after 60 req/min, admin exempt, correct headers
- [ ] All 4 new test files + 2 extended test files pass (ruff + pytest)

---

## Out of Scope for Phase 2

| Item | Phase |
|------|-------|
| SSE streaming | P3 |
| Config management API | P3 |
| Webhook notifications | P3 |
| CORS configuration | P3 |
| Structured JSON logging | P3 |
| systemd service file | P3 |
| Integration tests | P3 |

*Source: [`docs/blueprint-backend-api.md`](../../blueprint-backend-api.md), [`docs/PRD-backend-api.md`](../../PRD-backend-api.md)*
