# Repository Guidelines

## Project Overview

PortalOnline GMap Scraper -- a Python CLI tool that scrapes business leads from Google Maps using Camoufox (anti-detection Firefox browser). Tuned for VPS environments (4 CPU / 5GB RAM). Collects URLs first, then processes them with a single worker page to stay within Camoufox's memory limits (~900MB peak).

## Project Structure (Monorepo)

```
├── backend/                    # Python API backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI/Flask entry point
│   │   ├── config.py          # Settings from .env
│   │   ├── api/               # API routes
│   │   │   ├── __init__.py
│   │   │   ├── routes_leads.py
│   │   │   └── routes_health.py
│   │   ├── models/            # Data models
│   │   │   ├── __init__.py
│   │   │   └── lead.py
│   │   ├── services/          # Business logic
│   │   │   ├── __init__.py
│   │   │   └── scraper_service.py
│   │   └── utils/             # Shared utilities
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_models/
│   ├── pyproject.toml
│   └── .env
│
├── frontend/                   # Web frontend (Vue/Svelte/Astro)
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page views
│   │   ├── stores/            # State management
│   │   ├── services/          # API client services
│   │   ├── types/             # TypeScript types
│   │   └── utils/             # Frontend utilities
│   ├── public/
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── shared/                     # Shared types/configs
│   ├── types/
│   └── constants/
│
├── scripts/                    # Build/deploy scripts
├── docs/                       # Documentation
├── .env                        # Root env (gitignored)
└── README.md
```

### Monorepo Best Practices
- **Backend**: Python 3.12+ dengan FastAPI/Flask, modular structure
- **Frontend**: Vue/Svelte/Astro dengan TypeScript, component-based
- **Shared**: Types dan constants yang dipakai bersama
- **Independent deployability**: Setiap package bisa di-deploy terpisah
- **Shared tooling**: Ruff, ESLint, Prettier di root level

## Build, Test, and Development Commands

All commands run from the project root. Use `uv` (project uses `uv.lock`).

```bash
# Install dependencies
uv sync

# Run all tests
.venv/bin/python -m pytest tests/ -v

# Run a single test file
.venv/bin/python -m pytest tests/test_scraper.py -v

# Run tests matching a pattern
.venv/bin/python -m pytest tests/ -k "test_scrape" -v

# Lint
.venv/bin/python -m ruff check .

# Format check
.venv/bin/python -m ruff format --check .

# Auto-format
.venv/bin/python -m ruff format .
```

## Coding Style & Naming Conventions

- **Python 3.12+** required (type hints with `X | Y` union syntax, `list[str]` lowercase generics).
- **Formatter/Linter**: Ruff. Line length 88, double quotes, space indentation.
- **Ruff rules**: `E` (pycodestyle), `F` (pyflakes), `I` (isort), `N` (pep8-naming), `W` (warnings), `UP` (pyupgrade).
- **Private functions**: prefixed with `_` (e.g., `_memory_guard`, `_random_delay`).
- **Constants**: `UPPER_SNAKE_CASE` in `config.py`.
- **Async**: all scraping functions are `async def`; use `asyncio` patterns throughout.

## Testing Guidelines

- **Framework**: pytest + pytest-asyncio (`asyncio_mode = "auto"`).
- **Test location**: `tests/` directory, files named `test_*.py`.
- **Mocking**: Browser interactions are fully mocked (`unittest.mock.AsyncMock`). Never make real network calls in tests.
- **Test naming**: `test_<action>_<condition>` (e.g., `test_returns_none_on_failure`).
- **Run tests before committing** to ensure no regressions.

## Environment Configuration

All runtime settings are in `.env` (loaded by `config.py`). Key variables:

| Variable | Default | Description |
|---|---|---|
| `LEADS` | 25 | Target lead count |
| `MAX_TAB_ALLOWED` | 1 | Concurrent browser tabs (Camoufox limit: 1) |
| `BATCH_SIZE` | 5 | URLs per batch before cooldown |
| `COOLDOWN_SEC` | 8 | Pause between batches (seconds) |
| `MEM_LIMIT_MB` | 8192 | Pause when RAM below threshold |
| `CPU_LIMIT_PERCENT` | 50 | Pause when CPU load above threshold |
| `INTER_QUERY_COOLDOWN` | 12 | Pause between keyword queries (smart search) |
| `MAX_URLS_PER_QUERY` | 60 | Max URLs to collect per query |
| `MAX_RETRIES` | 2 | Retry attempts for failed URLs |
| `PROCESS_NICE` | 15 | OS scheduling priority 0-19 |
| `HEADLESS` | true | Run browser without UI |
| `DEBUG` | false | Enable debug logging |

## Commit & Pull Request Guidelines

- Commit messages: short imperative subject (e.g., "Fix config syntax error", "Add batch cooldown").
- Keep commits focused on one logical change.
- Run `ruff check .` and `pytest tests/` before pushing.
- PR descriptions should explain the "why" and reference any related issues.

## Architecture Notes

1. **`collect_lead_links()`** scrolls the Google Maps feed and collects place URLs. Retries page.goto up to 3 times on timeout. Injects JS error handler to suppress Playwright Firefox driver crash bug.
2. **`extract_lead_data()`** navigates to each place page and extracts business info via JS injection.
3. **`extract_lead_data_with_retry()`** wraps extraction with exponential backoff retry (1-2s base, doubles per attempt).
4. **`_page_worker()`** manages a persistent browser tab, processes URLs from queue with batch cooldown and graduated resource guards (checked every 3 URLs). Drains queue gracefully on browser crash.
5. **`process_all_leads()`** orchestrates concurrent tab workers with batching and cooldowns.
6. **`scrape()`** is the main orchestrator (Camoufox browser lifecycle). Pipeline: collect all URLs first, then create worker page(s) and process. Workers are NOT created before link collection (Camoufox crashes with 3+ concurrent pages).
7. **`scrape_smart()`** extends `scrape()` with keyword variations from `CATEGORY_VARIATIONS`, restarting browser between queries to release memory. Stops early after 2 consecutive queries with 0 new leads.

### Performance Optimizations

- **Camoufox low-memory config**: `block_images`, `block_webgl`, `exclude_addons` (removes uBlock Origin). Reduces browser RAM from ~950MB to ~770MB idle.
- **Page error suppression**: injects `window.onerror` handler into all pages to prevent Playwright Firefox driver crash (TypeError in FFBrowserContext when pageError.location is undefined).
- **Retry on page load**: `collect_lead_links` retries `page.goto` up to 3 times with 5s/10s/15s backoff.
- **Two-phase pipeline**: collect URLs first (1 page), then process (1 worker page). Avoids Camoufox crash with 3+ concurrent pages.
- **Worker crash recovery**: `_page_worker` catches browser connection errors and drains the queue so `process_all_leads` can finish cleanly.
- **Early termination**: `scrape_smart` stops after 2 consecutive queries yielding 0 new leads.
- **Graduated memory guard**: 5s/10s/20s pauses based on memory severity (instead of flat 30s).
- **Resource blocking**: images, media, fonts, stylesheets, websocket, ping are blocked via Playwright route.
- **Exponential retry backoff**: 1-2s base, doubles per attempt.
- **Guard frequency**: memory/CPU guards checked every 3 URLs instead of every URL.

### Known Limitations

- **MAX_TAB_ALLOWED must be 1**: Camoufox (Firefox) crashes with 3+ concurrent pages. 2 worker pages + 1 collect page = crash. This is a Camoufox/Playwright limitation.
- **Camoufox RAM ~900MB per query**: 6 Firefox processes, not controllable via `dom.ipc.processCount` (Playwright overrides). Browser restart between queries releases 100%.
- **Playwright Firefox driver bug**: `pageError.location` can be undefined, crashing Node.js process. Mitigated by JS error injection into pages.

## Personal & Project Memories
- Refer to `~/.factory/memories.md` for overall coding preferences and stack decisions (e.g., preference for Vue/Svelte/Astro, Go, Python).
- Refer to `.factory/memories.md` for specific project constraints, architectural decisions, and known limitations (e.g., Camoufox RAM limits, two-phase pipeline).

## Coding Standards & Rules
Follow the conventions documented in:
- `.factory/rules/python.md` - Python and Async patterns
- `.factory/rules/testing.md` - Pytest and Mocking conventions
- `.factory/rules/security.md` - Secrets, resource safety, and crawler footprints
- `.factory/rules/code-quality.md` - Code length limits, splitting rules, best practices

## Token Efficiency & Validation (Hooks)
- The project has **automatic PostToolUse hooks** enabled (`format.sh`, `test-on-edit.sh`, `scan-secrets.sh`).
- **You do NOT need to manually run `ruff` or `pytest`** after editing a file, as the hooks will run them automatically and verify your changes in the same turn.
- To save tokens, avoid exploring the filesystem extensively if you can use the IDE plugin context. Always start by reading the specific file mentioned.
- If you need a fast smoke test manually, run: `pytest tests/ -v --maxfail=1`.

## Planning Documents

Project planning follows a layered document hierarchy. When implementing features, reference the appropriate document:

| Document | Layer | Purpose | When to Read |
|---|---|---|---|
| [`ROADMAP.md`](ROADMAP.md) | Product Direction | Phases, milestones, timeline, open decisions | Before starting any new work |
| Blueprint (docs/) | Strategy | Workstreams, risks, key decisions, deployment model | When planning implementation approach |
| PRD (docs/) | Requirements | FRs, NFRs, data models, SQL schemas, endpoint specs | When writing code, tests, or reviewing PRs |

**Rule of thumb**: ROADMAP answers "what and when", Blueprint answers "how we're organizing the work", PRD answers "exactly what to build".
