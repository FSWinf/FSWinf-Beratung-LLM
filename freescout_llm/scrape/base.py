"""
Base classes for web scrapers.
"""

import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import scrapy
from markdownify import markdownify as md
from scrapy.crawler import CrawlerProcess


def sanitize_filename(path: str) -> str:
    """
    Sanitizes a URL path to be a valid filename.
    Replaces slashes with underscores and removes invalid characters.

    Args:
        path: URL path to sanitize

    Returns:
        Sanitized filename safe for filesystem use
    """
    # Remove leading/trailing slashes and replace others with an underscore
    sanitized = path.strip("/").replace("/", "_")
    # Keep only alphanumeric characters, underscores, and hyphens
    sanitized = "".join([c for c in sanitized if c.isalnum() or c in ("_", "-")])
    # If the sanitized name is empty (like for the homepage), use 'index'
    return sanitized if sanitized else "index"


def clean_informatics_content(content: str, filename: str) -> str:
    """
    Clean informaticstuwienacat content by removing specific sections.

    Args:
        content: Original markdown content
        filename: Name of the file being processed

    Returns:
        Cleaned markdown content
    """
    # Only apply to specific file patterns
    if not (
        filename.startswith("people_")
        or filename.startswith("orgs_")
        or filename.startswith("foci")
        or filename in ["ai.md", "awards.md"]
    ):
        return content

    lines = content.split("\n")
    cleaned_lines = []

    for line in lines:
        # Check if this line starts one of the sections we want to remove
        if (
            line.strip().startswith("# Courses")
            or line.strip().startswith("# Projects")
            or line.strip().startswith("# Publications")
            or line.strip().startswith("# Recent Projects")
            or line.strip().startswith("# Research")
            or line.strip().startswith("# Awards by Year")
        ):
            break
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def remove_data_images(content: str) -> str:
    """
    Remove embedded data images from markdown content.

    Finds patterns like:
    ![Alt text](data:image/jpeg;base64,...)
    ![Alt text](data:image/png;base64,...)
    ![[Translate to English:] Alt text](data:image/png;base64,...)
    etc.

    Args:
        content: Original markdown content

    Returns:
        Cleaned markdown content without data images
    """
    # Pattern to match embedded data images
    # Matches: ![...](data:image/...;base64,...)
    # The [^\]]* allows for any characters including brackets within the alt text
    pattern = r"!\[(?:[^\[\]]|\[[^\]]*\])*\]\(data:image/[^;]+;base64,[^)]+\)"

    # Remove the data images
    cleaned_content = re.sub(pattern, "", content)

    return cleaned_content


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.
    """

    def __init__(self, base_url: str, output_dir: str):
        """
        Initialize the scraper.

        Args:
            base_url: The base URL to scrape
            output_dir: Directory to save scraped content
        """
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def run(self) -> None:
        """
        Run the scraper.
        """
        pass

    def save_content(self, content: str, filename: str) -> None:
        """
        Save content to a file with automatic cleaning.

        Args:
            content: Content to save
            filename: Name of the file (will be sanitized)
        """
        safe_filename = sanitize_filename(filename)
        if not safe_filename.endswith(".md"):
            safe_filename += ".md"

        # Apply content cleaning
        cleaned_content = remove_data_images(content)
        cleaned_content = clean_informatics_content(cleaned_content, safe_filename)

        filepath = self.output_dir / safe_filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cleaned_content)


class ScrapyBaseScraper(BaseScraper):
    """
    Base class for Scrapy-based scrapers.
    """

    def __init__(self, base_url: str, output_dir: str, spider_class: type):
        """
        Initialize the Scrapy scraper.

        Args:
            base_url: The base URL to scrape
            output_dir: Directory to save scraped content
            spider_class: The Scrapy spider class to use
        """
        super().__init__(base_url, output_dir)
        self.spider_class = spider_class

    def run(self) -> None:
        """
        Run the Scrapy spider.
        """
        process = CrawlerProcess(
            {
                "USER_AGENT": "FreeScout-LLM-Scraper",
                "ROBOTSTXT_OBEY": True,
                "DOWNLOAD_DELAY": 1,
                "RANDOMIZE_DOWNLOAD_DELAY": True,
                "AUTOTHROTTLE_ENABLED": True,
                "AUTOTHROTTLE_START_DELAY": 1,
                "AUTOTHROTTLE_MAX_DELAY": 3,
                "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
            }
        )

        process.crawl(
            self.spider_class, base_url=self.base_url, output_dir=str(self.output_dir)
        )
        process.start()


class BaseWebsiteSpider(scrapy.Spider):
    """
    Base spider class with common functionality.
    """

    def __init__(self, base_url: str, output_dir: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [base_url]
        self.allowed_domains = [urlparse(base_url).netloc]
        self.output_dir = output_dir

        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger.info(f"Saving markdown files to: {self.output_dir}")

    def extract_main_content(self, response) -> Optional[str]:
        """
        Extract main content from response. Override in subclasses.

        Args:
            response: Scrapy response object

        Returns:
            Main content as string or None if extraction fails
        """
        # Default implementation - extract from main, article, or body
        content_selectors = ["main", "article", ".main-content", ".content", "body"]

        for selector in content_selectors:
            content = response.css(selector).get()
            if content:
                return md(content)

        return None

    def save_page_content(self, response, content: str) -> None:
        """
        Save page content to file.

        Args:
            response: Scrapy response object
            content: Content to save
        """
        # Extract the path from the URL for the filename
        parsed_url = urlparse(response.url)
        filename = sanitize_filename(parsed_url.path)

        if not filename.endswith(".md"):
            filename += ".md"

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {response.url}\n\n")
            f.write(content)

        self.logger.info(f"Saved content to: {filepath}")
