"""PortalOnline GMap Scraper - A library for scraping business leads."""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from .config import (
    ADMIN_API_KEY,
    API_HOST,
    API_KEY,
    API_PORT,
    BATCH_SIZE,
    CATEGORY_VARIATIONS,
    COOLDOWN_SEC,
    CSV_FILENAME,
    DEBUG,
    HEADLESS,
    INTER_QUERY_COOLDOWN,
    MAX_TABS,
    MAX_URLS_PER_QUERY,
    MEM_LIMIT_MB,
    PROCESS_NICE,
    SAVE_AS_CSV,
    TARGET_LEADS,
)
from .scraper import (
    collect_lead_links,
    extract_lead_data,
    process_all_leads,
    scrape,
    scrape_smart,
)

__all__ = [
    "scrape",
    "scrape_smart",
    "collect_lead_links",
    "extract_lead_data",
    "process_all_leads",
    "TARGET_LEADS",
    "MAX_TABS",
    "HEADLESS",
    "SAVE_AS_CSV",
    "CSV_FILENAME",
    "DEBUG",
    "CATEGORY_VARIATIONS",
    "BATCH_SIZE",
    "COOLDOWN_SEC",
    "PROCESS_NICE",
    "MEM_LIMIT_MB",
    "MAX_URLS_PER_QUERY",
    "INTER_QUERY_COOLDOWN",
    "API_HOST",
    "API_PORT",
    "API_KEY",
    "ADMIN_API_KEY",
]
