"""
Google Maps Lead Scraper
========================

A high-performance library for extracting business leads from Google Maps.

Architecture:
    1. collect_lead_links()  - Scrolls Maps feed, collects place URLs
    2. extract_lead_data()   - Navigates to place page and extracts data
    3. _page_worker()        - Manages a persistent browser tab
    4. process_all_leads()   - Creates N workers to process URLs concurrently
    5. scrape()              - Main orchestrator

VPS Optimizations:
    - Process nice priority to yield CPU to other processes
    - Memory monitoring: pauses when available RAM drops below threshold
    - Batch processing with cooldown between batches
    - Max 1 tab by default (configurable) to prevent CPU saturation
    - Single await with proper timeout (no busy-loop slicing)
    - Resource blocking (images/media/fonts) to reduce bandwidth
    - Page pooling: Tabs are reused instead of created/destroyed per URL
    - Minimal viewport (800x600) reduces rendering overhead
"""

import asyncio
import gc
import logging
import os
import random
import re
from contextlib import suppress

from camoufox.addons import DefaultAddons
from camoufox.async_api import AsyncCamoufox

from .config import (
    BATCH_SIZE,
    CATEGORY_VARIATIONS,
    COOLDOWN_SEC,
    CPU_LIMIT_PERCENT,
    DELAY_MAX_SEC,
    DELAY_MIN_SEC,
    HEADLESS,
    INTER_QUERY_COOLDOWN,
    MAX_RETRIES,
    MAX_TABS,
    MAX_URLS_PER_QUERY,
    MEM_LIMIT_MB,
    PROCESS_NICE,
    TARGET_LEADS,
)

logger = logging.getLogger(__name__)

_BLOCKED_RESOURCE_TYPES = frozenset(
    ("image", "media", "font", "ping", "websocket", "stylesheet")
)
_PLUS_CODE_RE = re.compile(r"[A-Z0-9]{4}\+[A-Z0-9]{2,3},?\s*")
_NAVIGATION_TIMEOUT_MS = 45_000
_DETAIL_SELECTOR_TIMEOUT_MS = 30_000

# Camoufox low-memory config: removes uBlock addon (~182MB savings)
_CAMOUFOX_LOW_MEM = dict(
    block_images=True,
    block_webgl=True,
    exclude_addons=list(DefaultAddons),
    i_know_what_im_doing=True,
)


# ---------------------------------------------------------------------------
# Resource management helpers
# ---------------------------------------------------------------------------


def _set_process_priority():
    """Lower process priority so it yields CPU to other tasks."""
    try:
        os.nice(PROCESS_NICE)
        logger.info(f"Process nice priority set to {PROCESS_NICE}")
    except (OSError, PermissionError) as exc:
        logger.debug(f"Could not set nice priority: {exc}")


def _get_available_ram_mb() -> int:
    """Return available system memory in MB (Linux/Unix)."""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except (FileNotFoundError, OSError, ValueError):
        pass
    # Fallback: assume enough memory if /proc/meminfo unavailable
    return MEM_LIMIT_MB + 1


async def _memory_guard():
    """Pause execution if system memory is critically low.

    Uses graduated wait: shorter pauses for borderline cases,
    longer pauses only when memory is critically low.
    """
    available = _get_available_ram_mb()
    if available < MEM_LIMIT_MB:
        ratio = available / MEM_LIMIT_MB if MEM_LIMIT_MB > 0 else 0
        if ratio < 0.25:
            wait_sec = 20
        elif ratio < 0.5:
            wait_sec = 10
        else:
            wait_sec = 5
        logger.warning(
            f"Low memory: {available}MB available (limit: {MEM_LIMIT_MB}MB). "
            f"Pausing {wait_sec}s to let system recover."
        )
        gc.collect()
        await asyncio.sleep(wait_sec)
        return True
    return False


async def _cpu_guard():
    """Pause execution if CPU usage exceeds limit."""
    try:
        load1, _, _ = os.getloadavg()
        num_cores = os.cpu_count() or 1
        cpu_pct = (load1 / num_cores) * 100
        if cpu_pct > CPU_LIMIT_PERCENT:
            wait = random.uniform(1.0, 2.0)
            logger.warning(
                f"High CPU: {cpu_pct:.0f}% (limit: {CPU_LIMIT_PERCENT}%). "
                f"Pausing {wait:.1f}s."
            )
            await asyncio.sleep(wait)
    except OSError:
        pass


def _force_gc():
    """Force garbage collection to free browser page memory."""
    collected = gc.collect()
    logger.debug(f"GC collected {collected} objects")


# ---------------------------------------------------------------------------
# Browser helpers
# ---------------------------------------------------------------------------


async def _block_heavy_resources(route):
    """Abort heavy resources (images, media, fonts) to improve performance."""
    if route.request.resource_type in _BLOCKED_RESOURCE_TYPES:
        await route.abort()
    else:
        await route.continue_()


# JS injected into pages to suppress uncaught errors that crash Playwright's
# Firefox driver (TypeError in FFBrowserContext when pageError.location is undefined)
_SUPPRESS_PAGE_ERRORS_JS = """
window.addEventListener('error', (e) => { e.preventDefault(); return true; });
window.addEventListener('unhandledrejection', (e) => { e.preventDefault(); });
"""


_EXTRACT_DATA_JS = """
() => {
    const h1 = document.querySelector('h1.DUwDvf');
    if (!h1) return null;
    const getText = el => {
        if (!el) return 'N/A';
        return el.innerText.replace(/\\n/g, ' ').trim();
    };
    // Rating: the large number displayed next to stars (e.g., "4.5")
    const ratingEl = document.querySelector('div.fontDisplayLarge');
    const rating = ratingEl ? ratingEl.innerText.trim() : 'N/A';
    // Review count: text like "(1,234)" near the rating, inside a button
    const reviewBtn = document.querySelector('button[data-item-id="reviews"] span');
    let reviewCount = 'N/A';
    if (reviewBtn) {
        const match = reviewBtn.innerText.match(/[\\d,.]+/);
        if (match) reviewCount = match[0].replace(/,/g, '');
    }
    return {
        name:        h1.innerText.trim(),
        address:     getText(document.querySelector('button[data-item-id="address"]')),
        phone:       getText(document.querySelector(
                         'button[data-item-id^="phone:tel:"]')),
        website:     getText(document.querySelector('a[data-item-id="authority"]')),
        rating:      rating,
        review_count: reviewCount,
    };
}
"""

_COLLECT_LINKS_JS = """
() => {
    const anchors = document.querySelectorAll('a[href*="/maps/place/"]');
    return [...anchors].map(a => a.href).filter(Boolean);
}
"""


def _clean_lead_data(data: dict) -> dict:
    """Clean address, phone, rating, and review count from scraped lead data."""
    addr = data.get("address", "N/A")
    if addr != "N/A":
        addr = _PLUS_CODE_RE.sub("", addr).strip().lstrip(", ").strip()
        data["address"] = addr

    phone = data.get("phone", "N/A")
    if phone != "N/A":
        phone = phone.replace("\u200b", "").strip()
        data["phone"] = phone

    # Normalize rating: keep as string "4.5" or "N/A"
    rating = data.get("rating", "N/A")
    if rating != "N/A":
        # Extract just the number from strings like "4.5 stars"
        match = re.match(r"(\d+\.?\d*)", rating)
        data["rating"] = match.group(1) if match else "N/A"

    # Normalize review count: remove commas, keep as string
    review_count = data.get("review_count", "N/A")
    if review_count != "N/A":
        review_count = review_count.replace(",", "").strip()
        if review_count.isdigit():
            data["review_count"] = review_count
        else:
            data["review_count"] = "N/A"

    return data


async def _random_delay():
    """Sleep a random interval to mimic human browsing."""
    delay = random.uniform(DELAY_MIN_SEC, DELAY_MAX_SEC)
    await asyncio.sleep(delay)


async def _cooldown_pause():
    """Pause between batches to let CPU and memory settle."""
    jitter = random.uniform(0.8, 1.2)
    wait = COOLDOWN_SEC * jitter
    logger.info(f"Batch cooldown: pausing {wait:.1f}s")
    await asyncio.sleep(wait)


# ---------------------------------------------------------------------------
# Link collection
# ---------------------------------------------------------------------------


async def collect_lead_links(
    browser,
    query: str,
    target: int = TARGET_LEADS,
    url_queue: asyncio.Queue[str | None] | None = None,
    skip_urls: set[str] | None = None,
    max_urls: int = MAX_URLS_PER_QUERY,
) -> list[str]:
    """
    Search Google Maps for a query and collect place URLs.

    Args:
        browser: Camoufox browser instance
        query: Search query (e.g., "Mobile Repair Shop in New York")
        target: Maximum number of lead URLs to collect
        url_queue: Optional queue to stream newly found URLs to consumers
        skip_urls: Set of URLs to skip (already collected in previous queries)
        max_urls: Hard cap on URLs to collect (prevents runaway scrolling)

    Returns:
        List of unique Google Maps place URLs
    """
    page = await browser.new_page(viewport={"width": 800, "height": 600})
    await page.add_init_script(_SUPPRESS_PAGE_ERRORS_JS)
    search_url = (
        f"https://www.google.com/maps/search/{query.replace(' ', '+')}?entry=ttu"
    )

    # Retry page.goto up to 3 times (Google can be slow/blocking)
    loaded = False
    for attempt in range(1, 4):
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=90_000)
            loaded = True
            break
        except Exception as exc:
            logger.warning(f"Page load attempt {attempt}/3 failed: {exc}")
            if attempt < 3:
                backoff = 5 * attempt
                logger.info(f"Retrying in {backoff}s...")
                await asyncio.sleep(backoff)

    if not loaded:
        logger.error(f"Failed to load Maps page after 3 attempts: {search_url}")
        await page.close()
        return []

    try:
        await page.wait_for_selector('div[role="feed"]', timeout=45_000)
    except Exception:
        logger.warning("Failed to load results feed")
        await page.close()
        return []

    try:
        update_btn = page.get_by_role("checkbox", name="Update results when map moves")
        if asyncio.iscoroutine(update_btn):
            update_btn = await update_btn
        await update_btn.click(timeout=5_000)
        with suppress(Exception):
            await update_btn.click(timeout=3_000)
    except Exception:
        logger.debug("Update-results checkbox not found or not clickable, continuing")

    lead_links: set[str] = set()
    stale_rounds = 0
    max_stale = 3
    scrape_all = target <= 0
    already_skipped = 0

    # Effective target: capped by max_urls
    effective_target = min(target, max_urls) if target > 0 else max_urls

    while (
        scrape_all or len(lead_links) < effective_target
    ) and stale_rounds < max_stale:
        hrefs = await page.evaluate(_COLLECT_LINKS_JS)
        new_links = 0

        for href in hrefs:
            if href in lead_links:
                continue

            # Skip URLs already collected in previous queries
            if skip_urls and href in skip_urls:
                already_skipped += 1
                continue

            lead_links.add(href)
            new_links += 1

            # Track in shared seen set for cross-query dedup
            if skip_urls is not None:
                skip_urls.add(href)

            if url_queue is not None:
                await url_queue.put(href)

            if not scrape_all and len(lead_links) >= effective_target:
                break

        if new_links == 0:
            stale_rounds += 1
        else:
            stale_rounds = 0

        if not scrape_all and len(lead_links) >= effective_target:
            break

        if len(lead_links) >= max_urls:
            logger.info(f"Reached max_urls cap ({max_urls}), stopping scroll")
            break

        scroll_js = (
            "() => { const feed = document.querySelector('div[role=\"feed\"]'); "
            "if (feed) feed.scrollTop = feed.scrollHeight; }"
        )
        await page.evaluate(scroll_js)
        await asyncio.sleep(0.8)  # Adaptive scroll - faster than original 1.5s

    await page.close()
    if already_skipped > 0:
        logger.info(f"Skipped {already_skipped} URLs already seen in previous queries")
    result = list(lead_links)
    if not scrape_all:
        result = result[:effective_target]
    logger.info(f"Collected {len(result)} URLs for query: {query!r}")
    return result


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------


async def extract_lead_data(page, url: str) -> dict | None:
    """
    Navigate to a place URL and extract business data.

    Args:
        page: Camoufox page instance
        url: Google Maps place URL

    Returns:
        Dictionary with name, address, phone, website or None if failed
    """
    try:
        await page.goto(
            url, wait_until="domcontentloaded", timeout=_NAVIGATION_TIMEOUT_MS
        )

        await page.wait_for_selector("h1.DUwDvf", timeout=_DETAIL_SELECTOR_TIMEOUT_MS)

        data = await page.evaluate(_EXTRACT_DATA_JS)
        return _clean_lead_data(data) if data else None
    except Exception as exc:
        logger.debug(f"Failed to extract data from {url}: {exc}")
        return None


async def extract_lead_data_with_retry(
    page, url: str, retries: int = MAX_RETRIES
) -> dict | None:
    """Extract lead data with retry logic and exponential backoff."""
    for attempt in range(1, retries + 1):
        data = await extract_lead_data(page, url)
        if data:
            return data
        if attempt < retries:
            backoff = random.uniform(1.0, 2.0) * (2 ** (attempt - 1))
            logger.debug(f"Retry {attempt}/{retries} for {url} in {backoff:.1f}s")
            await asyncio.sleep(backoff)
    return None


# ---------------------------------------------------------------------------
# Workers & orchestration
# ---------------------------------------------------------------------------


async def _page_worker(
    page,
    url_queue: asyncio.Queue[str | None],
    results: list,
    batch_size: int = BATCH_SIZE,
    cooldown_sec: float = COOLDOWN_SEC,
):
    """
    Worker that owns a persistent page and processes URLs from queue.

    Includes batch processing with cooldown and memory guard.

    Args:
        page: Camoufox page instance
        url_queue: Queue of URLs to process
        results: List to append successful results
        batch_size: URLs per batch before cooldown pause
        cooldown_sec: Seconds to pause between batches
    """
    processed_in_batch = 0
    processed_total = 0

    while True:
        url = await url_queue.get()
        try:
            if url is None:
                url_queue.task_done()
                return

            # Resource guards: check every 3 URLs to reduce overhead
            if processed_total % 3 == 0:
                await _memory_guard()
                await _cpu_guard()

            data = await extract_lead_data_with_retry(page, url)
            if data and data.get("phone", "N/A") != "N/A":
                results.append(data)

            processed_in_batch += 1
            processed_total += 1

            # Batch cooldown: pause after every batch_size URLs + GC
            if processed_in_batch >= batch_size:
                processed_in_batch = 0
                _force_gc()
                jitter = random.uniform(0.8, 1.2)
                wait = cooldown_sec * jitter
                logger.info(f"Batch cooldown: pausing {wait:.1f}s")
                await asyncio.sleep(wait)
            else:
                await _random_delay()

            url_queue.task_done()

        except Exception as exc:
            # Browser crash or connection lost - stop processing
            logger.warning(f"Worker error (browser may have crashed): {exc}")
            url_queue.task_done()
            # Drain remaining queue so process_all_leads can finish
            while True:
                try:
                    url_queue.get_nowait()
                    url_queue.task_done()
                except asyncio.QueueEmpty:
                    return


async def process_all_leads(
    browser,
    urls: list[str],
    max_tabs: int = MAX_TABS,
    batch_size: int = BATCH_SIZE,
    cooldown_sec: float = COOLDOWN_SEC,
) -> list[dict]:
    """
    Process multiple URLs concurrently using a pool of persistent pages.

    Args:
        browser: Camoufox browser instance
        urls: List of place URLs to scrape
        max_tabs: Maximum number of concurrent tabs (capped at 3)
        batch_size: URLs per batch before cooldown pause
        cooldown_sec: Seconds to pause between batches

    Returns:
        List of dictionaries containing business data
    """
    if not urls:
        return []

    safe_max_tabs = min(max_tabs, 3)
    num_tabs = max(1, min(safe_max_tabs, len(urls)))

    url_queue: asyncio.Queue[str | None] = asyncio.Queue()
    for url in urls:
        url_queue.put_nowait(url)
    for _ in range(num_tabs):
        url_queue.put_nowait(None)

    results: list[dict] = []

    pages = []
    for _ in range(num_tabs):
        p = await browser.new_page(viewport={"width": 800, "height": 600})
        await p.add_init_script(_SUPPRESS_PAGE_ERRORS_JS)
        await p.route("**/*", _block_heavy_resources)
        pages.append(p)

    tasks = [
        asyncio.create_task(
            _page_worker(page, url_queue, results, batch_size, cooldown_sec)
        )
        for page in pages
    ]

    await url_queue.join()
    await asyncio.gather(*tasks)

    for p in pages:
        try:
            await p.close()
        except Exception:
            pass

    return results


async def scrape(
    query: str,
    target: int = TARGET_LEADS,
    max_tabs: int = MAX_TABS,
    batch_size: int = BATCH_SIZE,
    cooldown_sec: float = COOLDOWN_SEC,
    browser=None,
    skip_urls: set[str] | None = None,
    max_urls: int = MAX_URLS_PER_QUERY,
) -> list[dict]:
    """
    Main entry point - scrape business leads from Google Maps.

    Args:
        query: Search query (e.g., "Restaurants in San Francisco")
        target: Number of leads to collect
        max_tabs: Number of concurrent tabs (default: 1 for VPS safety)
        batch_size: URLs per batch before cooldown pause
        cooldown_sec: Seconds to pause between batches
        browser: Existing Camoufox browser instance (reuse if provided)
        skip_urls: Set of URLs to skip (already collected in previous queries)

    Returns:
        List of dictionaries containing:
            - name: Business name
            - address: Physical address
            - phone: Phone number
            - website: Website URL
    """
    if target < 0:
        return []

    # Set low process priority for VPS friendliness
    _set_process_priority()

    # Cap tabs at 2 to prevent CPU overload
    safe_max_tabs = min(max_tabs, 3)
    logger.info(
        f"Starting scrape: query={query!r}, target={target}, "
        f"tabs={safe_max_tabs}, batch_size={batch_size}, "
        f"cooldown={cooldown_sec}s, available_ram={_get_available_ram_mb()}MB"
    )

    async def _run(browser_instance):
        num_tabs = safe_max_tabs if target == 0 else max(1, min(safe_max_tabs, target))
        results: list[dict] = []

        # Step 1: Collect all links first (1 page, no extra tabs)
        # Camoufox can't handle 3+ concurrent pages without timeouts
        fetch_target = 0 if target == 0 else int(target * 1.2)
        lead_urls = await collect_lead_links(
            browser_instance,
            query,
            target=fetch_target,
            skip_urls=skip_urls,
            max_urls=max_urls,
        )

        if not lead_urls:
            logger.info("No leads found for query")
            return []

        # Step 2: Create worker pages and process URLs
        url_queue: asyncio.Queue[str | None] = asyncio.Queue()
        for url in lead_urls:
            url_queue.put_nowait(url)

        pages = []
        for _ in range(num_tabs):
            page = await browser_instance.new_page(
                viewport={"width": 800, "height": 600}
            )
            await page.add_init_script(_SUPPRESS_PAGE_ERRORS_JS)
            await page.route("**/*", _block_heavy_resources)
            pages.append(page)

        tasks = [
            asyncio.create_task(
                _page_worker(page, url_queue, results, batch_size, cooldown_sec)
            )
            for page in pages
        ]

        # Signal workers to stop after all URLs are processed
        for _ in range(num_tabs):
            await url_queue.put(None)

        await url_queue.join()
        await asyncio.gather(*tasks)

        for page in pages:
            with suppress(Exception):
                await page.close()

        if not lead_urls:
            logger.info("No leads found for query")
            return []

        logger.info(f"Scraped {len(results)}/{len(lead_urls)} leads successfully")
        return results

    if browser is not None:
        return await _run(browser)

    async with AsyncCamoufox(headless=HEADLESS, **_CAMOUFOX_LOW_MEM) as new_browser:
        return await _run(new_browser)


# ---------------------------------------------------------------------------
# Smart search: multi-keyword with dedup
# ---------------------------------------------------------------------------

_SEPARATORS_RE = re.compile(r"\s+(?:di|in|daerah|area|sekitar|dekat)\s+", re.IGNORECASE)


def _parse_query(query: str) -> tuple[str, str]:
    """Split query into (category, location).

    Examples:
        "Rumah Makan di Sidomulyo" -> ("rumah makan", "Sidomulyo")
        "Hotel in Jakarta"         -> ("hotel", "Jakarta")
        "Bengkel daerah Kalianda"  -> ("bengkel", "Kalianda")
    """
    m = _SEPARATORS_RE.search(query)
    if m:
        category = query[: m.start()].strip()
        location = query[m.end() :].strip()
        return category, location
    # Fallback: treat entire query as category, empty location
    return query.strip(), ""


def _build_variations(category: str, location: str) -> list[str]:
    """Build list of search queries from category + location.

    Looks up CATEGORY_VARIATIONS for the matching key, then appends
    original category as first variation. If no match found, uses
    the original category as the sole variation.
    """
    cat_lower = category.lower()

    # Find matching key (exact or substring)
    variations: list[str] = []
    for key, synonyms in CATEGORY_VARIATIONS.items():
        if key in cat_lower or cat_lower in key:
            variations = list(synonyms)
            break

    # Always include the original category first
    if category.lower() not in [v.lower() for v in variations]:
        variations.insert(0, category)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for v in variations:
        vl = v.lower()
        if vl not in seen:
            seen.add(vl)
            unique.append(v)

    # Build full queries
    if location:
        return [f"{v} di {location}" for v in unique]
    return unique


def _dedup_key(lead: dict) -> str:
    """Generate dedup key from name + address (normalized).

    Uses name+address as primary key because:
    - phone can be N/A for many businesses (causes false merges)
    - same business can have different phone formats
    - name+address is nearly always unique per business
    """
    name = lead.get("name", "").strip().lower()
    address = lead.get("address", "").strip().lower()

    # Remove common noise from name for better matching
    name = re.sub(r"\s+", " ", name)

    # Remove plus codes and normalize address
    if address and address != "n/a":
        address = _PLUS_CODE_RE.sub("", address).strip().lstrip(", ").strip()
        address = re.sub(r"\s+", " ", address)
    else:
        address = ""

    return f"{name}|{address}"


async def scrape_smart(
    query: str,
    max_tabs: int = MAX_TABS,
    batch_size: int = BATCH_SIZE,
    cooldown_sec: float = COOLDOWN_SEC,
    inter_query_cooldown: float = INTER_QUERY_COOLDOWN,
) -> list[dict]:
    """Smart search: auto-generate keyword variations, scrape all, dedup.

    Restarts browser between queries to prevent memory leaks on low-RAM VPS.

    Args:
        query: User query (e.g., "Rumah Makan di Sidomulyo, Lampung Selatan")
        max_tabs: Concurrent tabs per query
        batch_size: URLs per batch
        cooldown_sec: Cooldown between batches
        inter_query_cooldown: Seconds to pause between different queries

    Returns:
        Deduplicated list of business leads
    """
    category, location = _parse_query(query)
    variations = _build_variations(category, location)

    logger.info(
        f"Smart search: category={category!r}, location={location!r}, "
        f"{len(variations)} keyword variations, "
        f"max_urls_per_query={MAX_URLS_PER_QUERY}"
    )
    for i, v in enumerate(variations, 1):
        logger.info(f"  [{i}/{len(variations)}] {v}")

    _set_process_priority()

    all_leads: dict[str, dict] = {}  # dedup_key -> lead
    seen_urls: set[str] = set()  # track all URLs across queries
    consecutive_empty = 0  # stop early if queries yield nothing new

    for i, var_query in enumerate(variations, 1):
        urls_before = len(seen_urls)
        logger.info(
            f"--- Query {i}/{len(variations)}: {var_query!r} "
            f"(seen_urls: {urls_before}) ---"
        )

        # Restart browser per query to release memory
        async with AsyncCamoufox(headless=HEADLESS, **_CAMOUFOX_LOW_MEM) as browser:
            results = await scrape(
                var_query,
                target=0,  # scrape all
                max_tabs=max_tabs,
                batch_size=batch_size,
                cooldown_sec=cooldown_sec,
                browser=browser,
                skip_urls=seen_urls,
                max_urls=MAX_URLS_PER_QUERY,
            )

        # Browser closed here - memory released
        _force_gc()
        logger.info(
            f"Browser closed, GC done. Available RAM: {_get_available_ram_mb()}MB"
        )

        new_count = 0
        for lead in results:
            key = _dedup_key(lead)
            if key not in all_leads:
                all_leads[key] = lead
                new_count += 1

        logger.info(
            f"Got {len(results)} leads, {new_count} new "
            f"(total unique: {len(all_leads)}, "
            f"new_urls: {len(seen_urls) - urls_before})"
        )

        # Early stop: skip remaining queries if 2 consecutive yield 0 new leads
        if new_count == 0:
            consecutive_empty += 1
            if consecutive_empty >= 2 and i < len(variations):
                remaining = len(variations) - i
                logger.info(
                    f"Early stop: {consecutive_empty} consecutive queries "
                    f"with 0 new leads, skipping {remaining} remaining queries"
                )
                break
        else:
            consecutive_empty = 0

        # Cooldown between queries
        if i < len(variations):
            jitter = random.uniform(0.8, 1.2)
            wait = inter_query_cooldown * jitter
            logger.info(f"Inter-query cooldown: {wait:.1f}s")
            await asyncio.sleep(wait)

    final = list(all_leads.values())
    logger.info(
        f"Smart search complete: {len(final)} unique leads "
        f"from {len(variations)} queries"
    )
    return final
