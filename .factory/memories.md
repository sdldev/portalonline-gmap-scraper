# Project Memories: portalonline-gmap-scraper

## Architecture Decisions
- Two-phase pipeline: collect all URLs first (1 page), then process with 1 worker page
- MAX_TAB_ALLOWED must stay at 1 (Camoufox crashes with 3+ concurrent pages)
- Browser restart between queries to release memory (Camoufox uses ~900MB per query)
- Resource blocking (images, media, fonts, stylesheets) via Playwright route for lower RAM usage

## Known Issues
- Camoufox spawns 6 Firefox processes per browser instance, not controllable via dom.ipc.processCount
- Playwright Firefox driver bug: pageError.location can be undefined, crashing Node.js process. Mitigated by JS error injection
- Memory peaks at ~900MB during scraping, graduated memory guard (5s/10s/20s pauses) is in place

## Performance Tuning
- block_images, block_webgl, exclude_addons reduces idle RAM from ~950MB to ~770MB
- Guard frequency: memory/CPU checks every 3 URLs (not every URL) to reduce overhead
- Exponential retry backoff: 1-2s base, doubles per attempt
- Early termination: scrape_smart stops after 2 consecutive queries with 0 new leads
