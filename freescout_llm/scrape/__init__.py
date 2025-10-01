"""
Web scraping package for FreeScout LLM.

This package contains scrapers for various educational and administrative websites
to build knowledge bases for the RAG pipeline.
"""

from .base import BaseScraper, ScrapyBaseScraper
from .freescout import FreescoutScraper
from .scrapy_scrapers import (
    HTUATScraper,
    InformaticsTUWienScraper,
    TUWienScraper,
    VOWiFSINFScraper,
    WINFATScraper,
)
from .tiss import TISSScraper

__all__ = [
    "BaseScraper",
    "ScrapyBaseScraper",
    "FreescoutScraper",
    "TISSScraper",
    "HTUATScraper",
    "InformaticsTUWienScraper",
    "TUWienScraper",
    "VOWiFSINFScraper",
    "WINFATScraper",
]
