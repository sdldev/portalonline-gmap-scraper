# PortalOnline GMap Scraper

Scrape business leads from Google Maps using Camoufox (anti-detection Firefox browser). Tuned for VPS (4 CPU / 5GB RAM). Monorepo with Python backend API + Vue 3 frontend.

## Status

```
Phase 1: Backend REST API -- Complete
Phase 2: Web Frontend -- Complete
Phase 3: Advanced Features -- Planned
```

See [ROADMAP.md](ROADMAP.md) for full product direction and milestones.

## Quick Start

```bash
# Install backend
cd backend && uv sync

# Run scraper via CLI
cd backend && .venv/bin/python manage.py

# Run API server
cd backend && .venv/bin/python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 9988

# Install & run frontend
cd frontend && npm install && npm run dev
```

## Features (Backend API)

- HTTP REST API on port 9988 (FastAPI + Uvicorn)
- Multi-user with RBAC (admin/user roles + API key auth)
- FIFO job queue with position tracking
- SQLite persistence (WAL mode, indexed, queryable)
- Real-time progress via SSE streaming
- Webhook notifications on job completion
- System health monitoring (RAM, CPU, disk)
- CLI user management (`backend/manage.py list|create|delete|seed`)
- Camoufox stealth browser scraping with memory guards

## Features (Frontend)

- Vue 3 SPA with TypeScript + TailwindCSS
- Pinia state management, Vue Router
- Auth pages (login/register)
- Dashboard with system health metrics
- Scrape workflow (new job, progress tracking)
- Results browser with search/filter
- User management (admin only)

## Documentation

| Document | Description |
|---|---|
| [ROADMAP.md](ROADMAP.md) | Product direction, phases, milestones |
| PRD (docs/) | Detailed requirements (FRs, NFRs, data models, API specs) |
| Blueprint (docs/) | Strategic execution plan (workstreams, decisions, risks) |
| [AGENTS.md](AGENTS.md) | Coding guidelines, test commands, architecture notes |

## Development

```bash
# Backend: install, test, lint, format
cd backend && uv sync
cd backend && .venv/bin/python -m pytest tests/ -v
cd backend && .venv/bin/python -m ruff check .
cd backend && .venv/bin/python -m ruff format .

# Frontend: install, dev server, type-check, test
cd frontend && npm install
cd frontend && npm run dev
cd frontend && npx vue-tsc --noEmit
cd frontend && npx playwright test
```

## Environment Configuration

Copy `.env.example` to `.env` (or see `backend/app/config.py` for defaults).

Key variables: `LEADS`, `MAX_TAB_ALLOWED`, `BATCH_SIZE`, `COOLDOWN_SEC`, `MEM_LIMIT_MB`, `HEADLESS`, `DEBUG`.

API-specific variables: `API_HOST`, `API_PORT`, `ADMIN_API_KEY`, `CORS_ORIGINS`, `MAX_JOB_DURATION_MINUTES`, `DATA_RETENTION_DAYS`.
