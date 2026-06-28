# PortalOnline GMap Scraper

High-performance Python library for extracting business leads from Google Maps using stealth browser (Camoufox).

## Features

- **Streaming pipeline** — workers start extracting data while links are still being collected
- **Concurrent tabs** — multiple browser tabs process leads simultaneously
- **Resource blocking** — skips images/media/fonts/stylesheet for faster extraction
- **Stealth browsing** — Camoufox avoids bot detection
- **Smart search** — auto-generates keyword variations with cross-query deduplication
- **VPS-tuned** — graduated memory guard, adaptive CPU throttling, batch cooldowns
- **Flexible output** — CSV file or JSON stdout

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Installation

### From PyPI

```bash
pip install portalonline-gmap-scraper
```

### From source (recommended for development)

```bash
git clone https://github.com/yourusername/portalonline-gmap-scraper.git
cd portalonline-gmap-scraper
uv sync --all-extras
```

## Usage

### CLI

```bash
# Basic — scrape 25 leads (default), save to scraped_data.csv
python -m portalonline_gmap_scraper.main "Restaurants in Jakarta"

# Custom lead count + concurrent tabs
python -m portalonline_gmap_scraper.main "Plumbers in NYC" --leads 50 --tabs 4

# JSON output to stdout
python -m portalonline_gmap_scraper.main "Coffee shops in Tokyo" --json

# Custom output filename
python -m portalonline_gmap_scraper.main "Hotels in Bali" -o hotels.csv

# Combine flags
python -m portalonline_gmap_scraper.main "Clinics in Singapore" --leads 100 --tabs 3 -o clinics.csv
```

If installed via `pip install -e .` or from PyPI:

```bash
portalonline-gmap-scraper "Restaurants in Jakarta" --leads 10 --json
```

### CLI Flags

| Flag | Default | Description |
| --- | --- | --- |
| `query` | (required) | Search query, e.g. `"Restaurants in San Francisco"` |
| `-o`, `--output` | `scraped_data.csv` | Output CSV filename |
| `--json` | off | Print results as JSON to stdout instead of CSV |
| `--leads` | `25` | Number of leads to collect |
| `--tabs` | `1` | Number of concurrent browser tabs |
| `--batch-size` | `5` | URLs per batch before cooldown pause |
| `--cooldown` | `8` | Seconds to pause between batches |
| `--scrape-all` | off | Scrape all available leads (ignores --leads) |
| `--smart` | off | Auto-generate keyword variations and dedup results |

### As a Library

```python
import asyncio
from portalonline_gmap_scraper import scrape

async def main():
    results = await scrape("Mobile Repair Shop in New York", target=10, max_tabs=3)

    for lead in results:
        print(f"Name: {lead['name']}")
        print(f"Address: {lead['address']}")
        print(f"Phone: {lead['phone']}")
        print(f"Website: {lead['website']}")

asyncio.run(main())
```

### Lower-level API

```python
import asyncio
from camoufox.async_api import AsyncCamoufox
from portalonline_gmap_scraper import collect_lead_links, extract_lead_data, process_all_leads

async def custom_flow():
    async with AsyncCamoufox(headless=True) as browser:
        # Phase 1: collect URLs only
        urls = await collect_lead_links(browser, "Cafes in Bandung", target=20)

        # Phase 2: extract data with custom tab count
        results = await process_all_leads(browser, urls, num_tabs=4)

    return results

asyncio.run(custom_flow())
```

## Environment Variables

Override defaults without changing code:

```bash
export LEADS=50              # Default lead count (default: 25)
export MAX_TAB_ALLOWED=4     # Default concurrent tabs (default: 1)
export BATCH_SIZE=5          # URLs per batch before cooldown (default: 5)
export COOLDOWN_SEC=8        # Pause between batches in seconds (default: 8)
export MEM_LIMIT_MB=4096     # Pause when RAM below threshold in MB (default: 8192)
export CPU_LIMIT_PERCENT=50  # Pause when CPU load above threshold (default: 50)
export INTER_QUERY_COOLDOWN=12  # Pause between keyword queries (default: 12)
export MAX_URLS_PER_QUERY=60 # Max URLs to collect per query (default: 60)
export HEADLESS=true         # Run browser headless (default: true)
export DEBUG=false           # Enable debug logging (default: false)
```

## Output Format

Each lead is a dictionary:

```json
{
    "name": "PA.SO.LA Restaurant",
    "address": "Sudirman Central Business District, Jakarta 12190",
    "phone": "(021) 25501993",
    "website": "ritzcarlton.com"
}
```

Fields return `"N/A"` when not available on the Google Maps listing.

## Project Structure

```
portalonline-gmap-scraper/
├── .github/                 # CI/CD workflows
│   ├── workflows/
│   │   ├── ci.yml           # Test + lint on push/PR
│   │   └── publish.yml      # Publish to PyPI on release
├── portalonline_gmap_scraper/      # Core package
│   ├── __init__.py          # Public API exports
│   ├── config.py            # Settings (env vars)
│   ├── main.py              # CLI entry point + CSV export
│   └── scraper.py           # Scraping engine
├── tests/                   # Test suite
│   ├── test_config.py
│   ├── test_main.py
│   └── test_scraper.py
├── pyproject.toml           # Package metadata + deps
└── README.md
```

## Development

### Setup

```bash
uv sync --all-extras
```

### Run tests

```bash
uv run pytest tests/ -v
```

### Lint + format

```bash
uv run ruff check .
uv run ruff format .
```

### Run from source

```bash
uv run python main.py "Restaurants in Jakarta" --leads 5 --json
```

## CI/CD

- **CI** — tests + lint on every push and PR
- **CD** — auto-publish to PyPI on GitHub release

## License

MIT License

## Disclaimer

This tool is for educational purposes. Scraping Google Maps may violate their Terms of Service. Use responsibly and at your own risk.
