"""
Migration script to move from old scrapers to new package.

This script provides utilities to run the new scrapers and
migrate existing configurations.
"""

import sys
from pathlib import Path

# Add the parent directory to Python path to import the new package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from freescout_llm.scrape import (
    FreescoutScraper,
    HTUATScraper,
    InformaticsTUWienScraper,
    TISSScraper,
    TUWienScraper,
    VOWiFSINFScraper,
    WINFATScraper,
)


def run_freescout_scraper():
    """Run the new FreeScout scraper."""
    print("Running FreeScout scraper...")
    scraper = FreescoutScraper()
    scraper.run()


def run_tiss_scraper():
    """Run the new TISS scraper."""
    print("Running TISS scraper...")
    scraper = TISSScraper()
    scraper.run()


def run_htu_scraper():
    """Run the new HTU scraper."""
    print("Running HTU scraper...")
    scraper = HTUATScraper()
    scraper.run()


def run_informatics_scraper():
    """Run the new Informatics scraper."""
    print("Running Informatics scraper...")
    scraper = InformaticsTUWienScraper()
    scraper.run()


def run_tuwien_scraper():
    """Run the new TUWien scraper."""
    print("Running TUWien scraper...")
    scraper = TUWienScraper()
    scraper.run()


def run_vowi_scraper():
    """Run the new VoWi scraper."""
    print("Running VoWi scraper...")
    scraper = VOWiFSINFScraper()
    scraper.run()


def run_winf_scraper():
    """Run the new WINF scraper."""
    print("Running WINF scraper...")
    scraper = WINFATScraper()
    scraper.run()


def run_all_scrapers():
    """Run all scrapers."""
    scrapers = [
        ("FreeScout", run_freescout_scraper),
        ("TISS", run_tiss_scraper),
        ("HTU", run_htu_scraper),
        ("Informatics", run_informatics_scraper),
        ("TUWien", run_tuwien_scraper),
        ("VoWi", run_vowi_scraper),
        ("WINF", run_winf_scraper),
    ]

    for name, runner in scrapers:
        print(f"\n{'='*50}")
        print(f"Running {name} scraper")
        print(f"{'='*50}")
        try:
            runner()
            print(f"✅ {name} scraper completed successfully")
        except Exception as e:
            print(f"❌ {name} scraper failed: {e}")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run new scrapers")
    parser.add_argument(
        "scraper",
        choices=[
            "freescout",
            "tiss",
            "htu",
            "informatics",
            "tuwien",
            "vowi",
            "winf",
            "all",
        ],
        help="Scraper to run",
    )

    args = parser.parse_args()

    runners = {
        "freescout": run_freescout_scraper,
        "tiss": run_tiss_scraper,
        "htu": run_htu_scraper,
        "informatics": run_informatics_scraper,
        "tuwien": run_tuwien_scraper,
        "vowi": run_vowi_scraper,
        "winf": run_winf_scraper,
        "all": run_all_scrapers,
    }

    runners[args.scraper]()
