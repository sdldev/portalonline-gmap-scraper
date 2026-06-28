"""
Configuration settings for PortalOnline GMap Scraper.

Environment Variables:
    LEADS: Number of leads to collect (default: 25)
    MAX_TAB_ALLOWED: Maximum concurrent tabs (default: 1 for VPS safety)
    HEADLESS: Run browser in headless mode (default: true)
    MAX_RETRIES: Retry attempts for failed URLs (default: 2)
    BATCH_SIZE: URLs per batch before cooldown (default: 5)
    COOLDOWN_SEC: Seconds to pause between batches (default: 8)
    PROCESS_NICE: OS scheduling priority 0-19, higher=nicer (default: 15)
    MEM_LIMIT_MB: Pause processing when available RAM below this (default: 8192)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (where pyproject.toml lives)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Scraper Settings
TARGET_LEADS = int(os.getenv("LEADS", "25"))
MAX_TABS = int(os.getenv("MAX_TAB_ALLOWED", "1"))
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

# Retry & Throttling
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
DELAY_MIN_SEC = 1.0
DELAY_MAX_SEC = 2.0

# Batch processing - prevents CPU saturation on VPS
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5"))
COOLDOWN_SEC = float(os.getenv("COOLDOWN_SEC", "8"))

# Process priority (0=normal, 10=nice, 19=very nice)
PROCESS_NICE = int(os.getenv("PROCESS_NICE", "15"))

# Memory safety threshold in MB - pause if available RAM drops below this
MEM_LIMIT_MB = int(os.getenv("MEM_LIMIT_MB", "8192"))
CPU_LIMIT_PERCENT = int(os.getenv("CPU_LIMIT_PERCENT", "50"))

# Smart search: max URLs to collect per keyword query (prevents runaway scrolling)
MAX_URLS_PER_QUERY = int(os.getenv("MAX_URLS_PER_QUERY", "60"))

# Smart search: seconds to pause between keyword queries for GC & RAM recovery
INTER_QUERY_COOLDOWN = float(os.getenv("INTER_QUERY_COOLDOWN", "12"))

# Output Settings
SAVE_AS_CSV = True
CSV_FILENAME = "scraped_data.csv"

# Development Settings
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# --- Backend API config ---
MAX_JOB_DURATION_MINUTES = int(os.getenv("MAX_JOB_DURATION_MINUTES", "30"))
MAX_TARGET_PER_JOB = int(os.getenv("MAX_TARGET_PER_JOB", "500"))
DATA_DIR = os.getenv("DATA_DIR", "data")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
DISK_USAGE_WARN_PERCENT = int(os.getenv("DISK_USAGE_WARN_PERCENT", "80"))
DISK_USAGE_LIMIT_PERCENT = int(os.getenv("DISK_USAGE_LIMIT_PERCENT", "90"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DATA_RETENTION_DAYS = int(os.getenv("DATA_RETENTION_DAYS", "90"))
AUTO_CLEANUP_HOUR = int(os.getenv("AUTO_CLEANUP_HOUR", "3"))


# API Server Settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "9988"))
API_KEY = os.getenv("API_KEY", "")  # Empty = no auth (dev only)
ADMIN_API_KEY = os.getenv(
    "ADMIN_API_KEY", ""
)  # Default admin API key (required for first boot)

# Smart search: keyword variations per category
# Keep only high-value core variations to avoid redundant queries
CATEGORY_VARIATIONS: dict[str, list[str]] = {
    "rumah makan": [
        "rumah makan",
        "restoran",
        "resto",
    ],
    "makanan": [
        "restoran",
        "rumah makan",
    ],
    "restoran": [
        "restoran",
        "rumah makan",
    ],
    "warung": [
        "warung nasi",
        "rumah makan",
    ],
    "cafe": [
        "kafe",
        "kedai kopi",
        "coffee shop",
    ],
    "hotel": [
        "hotel",
        "penginapan",
        "guest house",
    ],
    "toko": [
        "toko",
        "minimarket",
        "warung",
    ],
    "bengkel": [
        "bengkel",
        "bengkel motor",
        "servis kendaraan",
    ],
    "apotek": [
        "apotek",
        "apotik",
        "toko obat",
    ],
    "sekolah": [
        "sekolah",
        "madrasah",
        "pondok pesantren",
    ],
}
