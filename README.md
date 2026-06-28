# PortalOnline GMap Scraper

Scrape business leads from Google Maps using Camoufox (anti-detection Firefox browser). Tuned for VPS (4 CPU / 5GB RAM). **Now evolving from CLI tool into a REST API platform.**

## Status

```
Phase 1: Backend REST API -- In Development
Phase 2: Web Frontend -- Planned
Phase 3: Advanced Features -- Planned
```

See [ROADMAP.md](ROADMAP.md) for full product direction and milestones.

## Quick Start

```bash
# Install
uv sync

# Run scraper via CLI
.venv/bin/python -m portalonline_gmap_scraper.main

# Run API server (Phase 1 -- in development)
# .venv/bin/python -m portalonline_gmap_scraper.server
```

## Features (Current -- CLI)

- Google Maps business lead extraction (name, address, phone, website, rating, reviews)
- Camoufox stealth browser (anti-detection)
- Smart search with keyword variations
- Two-phase pipeline: URL collection then data extraction
- Memory guards for VPS stability (~900MB peak per query)
- Batch cooldown and exponential retry

## Features (Phase 1 -- Backend API)

- HTTP REST API on port 9988 (FastAPI + Uvicorn)
- Multi-user with RBAC (admin/user roles + API key auth)
- FIFO job queue with position tracking
- SQLite persistence (WAL mode, indexed, queryable)
- Real-time progress via SSE streaming
- Webhook notifications on job completion
- System health monitoring (RAM, CPU, disk)
- Data retention and auto-cleanup

## Documentation

| Document | Description |
|---|---|
| [ROADMAP.md](ROADMAP.md) | Product direction, phases, milestones |
| PRD (docs/) | Detailed requirements (FRs, NFRs, data models, API specs) |
| Blueprint (docs/) | Strategic execution plan (workstreams, decisions, risks) |
| [AGENTS.md](AGENTS.md) | Coding guidelines, test commands, architecture notes |

## Development

```bash
# Run tests
.venv/bin/python -m pytest tests/ -v

# Lint
.venv/bin/python -m ruff check .

# Format
.venv/bin/python -m ruff format .
```

## Environment Configuration

Copy `.env.example` to `.env` (or see `portalonline_gmap_scraper/config.py` for defaults).

Key variables: `LEADS`, `MAX_TAB_ALLOWED`, `BATCH_SIZE`, `COOLDOWN_SEC`, `MEM_LIMIT_MB`, `HEADLESS`, `DEBUG`.

API-specific variables (Phase 1): `API_HOST`, `API_PORT`, `ADMIN_API_KEY`, `CORS_ORIGINS`, `MAX_JOB_DURATION_MINUTES`, `DATA_RETENTION_DAYS`.
