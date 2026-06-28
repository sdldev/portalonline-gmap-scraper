"""CLI entry point for Google Maps Lead Generator."""

import argparse
import asyncio
import csv
import json
import logging
import sys

from .config import BATCH_SIZE, COOLDOWN_SEC, CSV_FILENAME, MAX_TABS, TARGET_LEADS
from .scraper import scrape, scrape_smart

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def save_to_csv(results: list[dict], filename: str = CSV_FILENAME):
    """Save results to CSV file."""
    if not results:
        return
    field_names = results[0].keys()
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"Data saved to {filename}")


async def main():
    parser = argparse.ArgumentParser(
        description="Google Maps Lead Generator - Extract business leads"
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Search query (e.g., 'Restaurants in San Francisco')",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="scraped_data.csv",
        help="Output CSV filename",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON to stdout",
    )
    parser.add_argument(
        "--leads",
        type=int,
        default=TARGET_LEADS,
        help=f"Number of leads to collect (default: {TARGET_LEADS})",
    )
    parser.add_argument(
        "--scrape-all",
        action="store_true",
        dest="scrape_all",
        help="Scrape all available leads in the area (ignores --leads)",
    )
    parser.add_argument(
        "--tabs",
        type=int,
        default=MAX_TABS,
        help=f"Number of concurrent browser tabs (default: {MAX_TABS})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        dest="batch_size",
        help=f"URLs per batch before cooldown pause (default: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=COOLDOWN_SEC,
        help=f"Seconds to pause between batches (default: {COOLDOWN_SEC})",
    )
    parser.add_argument(
        "--smart",
        action="store_true",
        help="Smart search: auto-generate keyword variations and dedup results",
    )

    args = parser.parse_args()

    if args.query is None:
        parser.print_help()
        sys.exit(0)

    logger.info(f"Starting lead generation for: {args.query}")
    if args.smart:
        results = await scrape_smart(
            args.query,
            max_tabs=args.tabs,
            batch_size=args.batch_size,
            cooldown_sec=args.cooldown,
        )
    else:
        target = 0 if args.scrape_all else args.leads
        results = await scrape(
            args.query,
            target=target,
            max_tabs=args.tabs,
            batch_size=args.batch_size,
            cooldown_sec=args.cooldown,
        )

    if results:
        logger.info(f"Total leads extracted: {len(results)}")

        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            save_to_csv(results, args.output)
    else:
        logger.warning("No results found")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
