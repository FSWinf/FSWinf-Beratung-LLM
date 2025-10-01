"""
Command-line interface for running scrapers.
"""

import argparse
import sys
from typing import Dict, Type

from .base import BaseScraper
from .freescout import FreescoutScraper
from .scrapy_scrapers import (
    HTUATScraper,
    InformaticsTUWienScraper,
    TUWienScraper,
    VOWiFSINFScraper,
    WINFATScraper,
)
from .tiss import TISSScraper


def get_scrapers() -> Dict[str, Type[BaseScraper]]:
    """
    Get available scrapers.

    Returns:
        Dictionary mapping scraper names to scraper classes
    """
    return {
        "freescout": FreescoutScraper,
        "tiss": TISSScraper,
        "htu": HTUATScraper,
        "informatics": InformaticsTUWienScraper,
        "tuwien": TUWienScraper,
        "vowi": VOWiFSINFScraper,
        "winf": WINFATScraper,
    }


def run_scraper(scraper_name: str, output_dir: str = None) -> None:
    """
    Run a specific scraper.

    Args:
        scraper_name: Name of the scraper to run
        output_dir: Optional custom output directory
    """
    scrapers = get_scrapers()

    if scraper_name not in scrapers:
        print(f"Unknown scraper: {scraper_name}")
        print(f"Available scrapers: {', '.join(scrapers.keys())}")
        return

    scraper_class = scrapers[scraper_name]

    try:
        if output_dir:
            scraper = scraper_class(output_dir=output_dir)
        else:
            scraper = scraper_class()

        print(f"Starting {scraper_name} scraper...")
        scraper.run()
        print(f"Completed {scraper_name} scraper.")

    except Exception as e:
        print(f"Error running {scraper_name} scraper: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="FreeScout LLM Web Scrapers")

    parser.add_argument(
        "scraper", help="Scraper to run", choices=list(get_scrapers().keys()) + ["all"]
    )

    parser.add_argument("--output-dir", help="Custom output directory")

    args = parser.parse_args()

    if args.scraper == "all":
        # Run all scrapers
        scrapers = get_scrapers()
        for scraper_name in scrapers:
            print(f"\n{'='*50}")
            print(f"Running {scraper_name} scraper")
            print(f"{'='*50}")
            run_scraper(scraper_name, args.output_dir)
    else:
        run_scraper(args.scraper, args.output_dir)


if __name__ == "__main__":
    main()
