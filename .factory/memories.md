# Project Memories: portalonline-gmap-scraper

## Monorepo Structure
- `backend/` — Python API (FastAPI) + Camoufox scraper
- `frontend/` — Vue 3 SPA (Vite + TypeScript + TailwindCSS)
- Vite dev server proxies `/api` -> `localhost:8000` (backend)

## Backend Architecture
- Two-phase pipeline: collect all URLs first (1 page), then process with 1 worker page
- MAX_TAB_ALLOWED must stay at 1 (Camoufox crashes with 3+ concurrent pages)
- Browser restart between queries to release memory (Camoufox uses ~900MB per query)
- Resource blocking (images, media, fonts, stylesheets) via Playwright route for lower RAM usage

## Backend Known Issues
- Camoufox spawns 6 Firefox processes per browser instance, not controllable via dom.ipc.processCount
- Playwright Firefox driver bug: pageError.location can be undefined, crashing Node.js process. Mitigated by JS error injection

## Backend Performance Tuning
- block_images, block_webgl, exclude_addons reduces idle RAM from ~950MB to ~770MB
- Guard frequency: memory/CPU checks every 3 URLs (not every URL) to reduce overhead
- Exponential retry backoff: 1-2s base, doubles per attempt
- Early termination: scrape_smart stops after 2 consecutive queries with 0 new leads

## Frontend Architecture
- Vue 3 Composition API with `<script setup lang="ts">` exclusively
- Pinia stores (composition API style) — `defineStore("name", () => { ... })`
- Vue Router with pages: Login, Dashboard, Scrape, Results, Users
- Custom UI component library in `src/components/ui/` (BaseButton, BaseCard, BaseModal, BaseTable, BaseBadge, ToastContainer)
- API client in `src/services/` using axios
- Testing: Playwright e2e only (no vitest/jest unit tests configured)

## Frontend Known Issues
- No ESLint/Prettier configured — formatting relies on vue-tsc type-checking only
- No unit test framework (vitest) — only Playwright e2e tests exist
- Playwright e2e starts backend server via webServer config — requires Python venv
