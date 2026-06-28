# ROADMAP: PortalOnline GMap Scraper Platform

**Last updated**: 2025-06-29
**Status**: Active development

---

## North Star

A **self-service lead generation platform** where operations teams trigger, monitor, and retrieve Google Maps business leads via API and web UI, without ever touching a terminal or VPS.

---

## Current State (Q2 2025)

```
[CLI Tool] ---> [CSV Files]
     ^
     |--- SSH ke VPS
     |--- Single user
     |--- No progress visibility
     |--- No job history
```

**What we have**: A working Camoufox-based Google Maps scraper (`scraper.py`) that runs via CLI. Collects URLs, extracts business data, writes CSV. Tuned for VPS (4 CPU / 5GB RAM). Battle-tested memory guards and error recovery.

**What we lack**: Any form of remote access, persistence, multi-user support, or integration surface.

---

## Phase 1: Backend REST API (Weeks 1-4)

**Goal**: Transform CLI tool into an HTTP-accessible scraping service with SQLite persistence, job queue, RBAC, and real-time streaming.

**Specs**: PRD and Blueprint available in `docs/`.

```
[HTTP Clients] ---> [FastAPI :9988] ---> [Job Queue (FIFO)] ---> [Camoufox Scraper]
                        |                        |                        |
                        v                        v                        v
                   [SQLite DB]            [SSE Stream]            [Batch Lead Writer]
                   - users                - progress              - dedup
                   - jobs                 - status_change         - WAL mode
                   - leads                - heartbeat
                   - audit_logs
```

### Milestones

| Milestone | Week | Deliverable | Success Gate |
|---|---|---|---|
| **M1: Walking Skeleton** | 1 | `POST /api/v1/jobs` returns job_id, scraper runs, results stored in SQLite | Manual curl: submit job, wait, get results via API |
| **M2: Core Platform** | 2 | User auth (RBAC), job queue (FIFO), health check, startup recovery, unit tests | Full lifecycle test: create user -> submit 3 jobs -> verify queue order -> retrieve results per user |
| **M3: Operational Ready** | 3 | Job listing/cancel, queue management, system monitoring, results query engine, audit logs, rate limiting, data cleanup | Admin dashboard data fully populated; disk guard rejects at 90% |
| **M4: Production Ship** | 4 | SSE streaming, webhooks, config API, structured logging, systemd service, integration tests | Server survives SIGTERM + restart; systemd auto-starts on boot; end-to-end test passes |

### Architecture Decisions (Evaluated)

| Decision | Choice | Rationale |
|---|---|---|
| Database | SQLite (WAL mode) | Zero-config, fits VPS 5GB. PostgreSQL unnecessary at current scale. |
| Framework | FastAPI | Native async (matches scraper), built-in SSE, auto OpenAPI docs. |
| Auth | API Key (hashed in DB) | Simplest for v1. JWT planned as parallel upgrade path in future phase. |
| Streaming | SSE | Unidirectional server->client sufficient. Simpler than WebSocket. |
| Concurrency | Single worker FIFO queue | Hard constraint from Camoufox (crashes with >1 page). |

---

## Phase 2: Web Frontend (Weeks 5-8) — Tentative

**Goal**: Build a browser-based UI for job submission, live progress tracking, and results exploration. No more curl.

**Specs**: TBD (separate PRD)

```
[Browser UI] ---> [Phase 1 API] ---> [Scraper Engine]
     |
     |--- Keyword form input (typeahead suggestions)
     |--- Live progress bar (SSE)
     |--- Results table (sort, filter, export)
     |--- Admin panel (users, queue, system health)
```

### Candidate Milestones

| Milestone | Focus |
|---|---|
| **M5: Operator UI** | Job submission form, live progress, results table with export |
| **M6: Admin UI** | User management, queue management, system dashboard |
| **M7: Polish** | Responsive mobile, dark mode, keyboard shortcuts |

*Technology choice (Vue/Svelte/Astro) to be decided in separate PRD. Frontend deploys independently from backend.*

---

## Phase 3: Advanced Features (Weeks 9+) — Tentative

**Goal**: Extend the platform with scheduling, integrations, and scale.

**Specs**: TBD (separate PRD per feature)

### Feature Candidates (from PRD Nice-to-Haves)

| Feature | Value | Effort |
|---|---|---|
| **Scheduled scraping** (cron-like) | Automasi penuh, tidak perlu trigger manual | Medium |
| **Google Sheets export** | Tim non-teknis bisa akses hasil di spreadsheet | Low |
| **Category variations CRUD API** | Operator bisa manage keyword variants tanpa edit config | Low |
| **JWT authentication** (parallel to API key) | Token short-lived, reduce DB lookup per request | Medium |
| **Telegram/Slack bot integration** | Trigger scrape + terima notifikasi dari chat | Medium |
| **Multi-VPS horizontal scaling** | Redis/PostgreSQL queue, multiple scraper workers | High |
| **OAuth2/SSO** | Enterprise identity provider integration | High |

---

## Timeline Overview

```
Q2 2025 (Now)
 |
 v
[CLI Tool] ----Phase 1 (4 weeks)----> [REST API Platform]
                                           |
                                      Phase 2 (4 weeks)
                                           |
                                           v
                                      [Web Frontend]
                                           |
                                      Phase 3 (ongoing)
                                           |
                                           v
                                      [Advanced Features]
```

```
Week:  1    2    3    4    5    6    7    8    9+
      |----|----|----|----|----|----|----|----|---->
      [ P1: Backend API  ] [ P2: Frontend ] [ P3: Advanced ]
            M1  M2  M3  M4
```

---

## Dependencies

```
Phase 1 (API) -----> Phase 2 (Frontend) -----> Phase 3 (Advanced)
     |
     |--- Camoufox stability (known limitation: 1 concurrent page)
     |--- VPS resource ceiling (5GB RAM, 4 CPU)
     |--- Python 3.12+ / uv package manager
```

**External dependencies**: None. SQLite is embedded. Camoufox/Playwright self-contained. Zero cloud services required.

---

## Open Decisions

| # | Decision | Options | Status | Target |
|---|---|---|---|---|
| D1 | Frontend framework | Vue / Svelte / Astro | Open | Phase 2 PRD |
| D2 | PostgreSQL migration | Stay on SQLite / Migrate at 100K leads / Migrate at 500K leads | Deferred | Monitor lead growth |
| D3 | JWT auth implementation | Parallel endpoint / Full replacement of API key | Deferred | Phase 3 |
| D4 | Frontend deploy strategy | Serve static from FastAPI / Separate VPS / Cloudflare Pages | Open | Phase 2 PRD |
| D5 | Horizontal scaling approach | Redis queue / PostgreSQL queue / Stay single-VPS | Deferred | Phase 3 |

---

## Documents Map

| Document | Purpose | Audience |
|---|---|---|
| [`ROADMAP.md`](ROADMAP.md) | High-level product direction, phases, milestones | All stakeholders |
| PRD (docs/) | Detailed requirements: FRs, NFRs, data models, endpoint specs | Engineering |
| Blueprint (docs/) | Strategic execution plan: workstreams, decisions, risks | Engineering, Product |
| [`AGENTS.md`](AGENTS.md) | Coding guidelines, test commands, architecture notes | AI agents, developers |

---

*This roadmap is a living document. Update milestones and dates as phases progress.*
