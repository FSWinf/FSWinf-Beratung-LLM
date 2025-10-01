"""
Scrapy-based scrapers for various websites.
"""

import hashlib
import json
import os
from urllib.parse import urlparse

from markdownify import markdownify as md
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule, Spider

from .base import (
    BaseScraper,
    clean_informatics_content,
    remove_data_images,
    sanitize_filename,
)


def generate_filename_hash(url: str) -> str:
    """Generate a short hash from the URL to ensure unique filenames."""
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:8]


def save_pdf_metadata(pdf_filepath: str, source_url: str) -> None:
    """
    Save PDF metadata to a JSON file alongside the PDF.

    Args:
        pdf_filepath: Path to the PDF file
        source_url: Original URL where the PDF was downloaded from
    """
    # Create JSON filename by replacing .pdf extension with .json
    json_filepath = pdf_filepath.rsplit(".", 1)[0] + ".json"

    metadata = {
        "source_url": source_url,
        "pdf_filename": os.path.basename(pdf_filepath),
        "type": "pdf_metadata",
    }

    try:
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save PDF metadata to {json_filepath}: {e}")


class HTUATSpider(CrawlSpider):
    """Spider for htu.at website."""

    name = "htu_spider"
    allowed_domains = ["htu.at"]
    start_urls = ["https://htu.at/"]

    rules = (
        Rule(
            LinkExtractor(allow=(r".*",)),
            callback="parse_item",
            follow=True,
        ),
    )

    def __init__(self, output_dir: str = "knowledge_base/htuat", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def parse_item(self, response):
        """Parse individual pages with HTU-specific logic."""
        self.logger.info(f"Scraping: {response.url}")

        # Extract the main content using HTU-specific CSS selector
        main_content_html = response.css("div#content").get()

        if not main_content_html:
            self.logger.warning(f"Could not find main content for {response.url}")
            return

        # Convert to markdown with metadata
        markdown_content = md(main_content_html, heading_style="ATX")
        source_url = response.url
        markdown_content = f"<!-- Source URL: {source_url} -->\n\n{markdown_content}"

        # Apply content cleaning (remove data images)
        markdown_content = remove_data_images(markdown_content)

        # Save content
        parsed_url = urlparse(response.url)
        filename = sanitize_filename(parsed_url.path) + ".md"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        self.logger.info(f"  -> Saved to {filepath}")

        # Follow links with HTU-specific filtering
        for href in response.css("a::attr(href)").getall():
            # Ignore specific URL types
            if (
                href.startswith("tel:")
                or href.startswith("javascript:")
                or href.startswith("mailto:")
                or href.startswith("#")
            ):
                continue

            # Get full URL and parse
            full_url = response.urljoin(href)
            parsed_href = urlparse(full_url)
            parts = parsed_href.path.split("/")

            # Skip year-based URLs (archives from 2000-2023)
            try:
                if int(parts[1]) in range(
                    2000, 2024
                ):  # Updated to 2024 for current year
                    continue
            except (ValueError, IndexError):
                pass

            yield response.follow(href, self.parse_item)

    def parse(self, response):
        """Override the default parse method to use parse_item for all pages."""
        return self.parse_item(response)


class InformaticsTUWienSpider(CrawlSpider):
    """Spider for informatics.tuwien.ac.at website."""

    name = "informatics_spider"
    allowed_domains = ["informatics.tuwien.ac.at"]
    start_urls = ["https://informatics.tuwien.ac.at"]

    rules = (
        Rule(
            LinkExtractor(allow=(r".*",), deny=(r"/news/.*",)),  # Exclude news links
            callback="parse_item",
            follow=True,
        ),
    )

    def __init__(
        self, output_dir: str = "knowledge_base/informaticstuwienacat", *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def parse_item(self, response):
        """Parse individual pages with custom logic for informatics.tuwien.ac.at."""
        self.logger.info(f"Scraping: {response.url}")

        # Check content type to handle different file types
        content_type = response.headers.get("Content-Type", b"").decode("utf-8").lower()
        parsed_url = urlparse(response.url)

        # Handle PDF files
        if "application/pdf" in content_type or parsed_url.path.lower().endswith(
            ".pdf"
        ):
            self.logger.info(f"Saving PDF: {response.url}")
            filename = sanitize_filename(parsed_url.path) + ".pdf"
            fpath = os.path.join(self.output_dir, filename)
            with open(fpath, "wb") as f:
                f.write(response.body)
            self.logger.info(f"  -> Saved PDF to {fpath}")

            # Save PDF metadata with source URL
            save_pdf_metadata(fpath, response.url)
            self.logger.info(f"  -> Saved PDF metadata for {response.url}")

            return  # Don't process links for PDFs

        # Skip other non-HTML file types
        if (
            "text/html" not in content_type
            and "application/xhtml" not in content_type
            and content_type  # Only check if content_type is not empty
            and not content_type.startswith("text/")
        ):
            self.logger.info(
                f"Skipping non-HTML file: {response.url} (Content-Type: {content_type})"
            )
            return

        # Extract the main content using multiple CSS selectors
        try:
            main_content_html = (
                response.css("main#main").get()
                or response.css("main#content").get()
                or response.css("main").get()
                or response.css("#content").get()
                or response.css(".content").get()
                or response.css("article").get()
            )
        except Exception as e:
            self.logger.warning(f"Could not parse CSS for {response.url}: {e}")
            return

        if not main_content_html:
            self.logger.warning(f"Could not find main content for {response.url}")
            return

        # Convert to markdown with metadata
        markdown_content = md(main_content_html, heading_style="ATX")
        source_url = response.url
        markdown_content = f"<!-- Source URL: {source_url} -->\n\n{markdown_content}"

        # Apply content cleaning for informaticstuwienacat
        markdown_content = remove_data_images(markdown_content)

        # Save content
        filename = sanitize_filename(parsed_url.path) + ".md"

        # Apply informaticstuwienacat-specific cleaning
        markdown_content = clean_informatics_content(markdown_content, filename)

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        self.logger.info(f"  -> Saved to {filepath}")

        # Follow links with custom filtering
        for href in response.css("a::attr(href)").getall():
            # Ignore specific URL types
            if (
                href.startswith("tel:")
                or href.startswith("javascript:")
                or href.startswith("mailto:")
                or href.startswith("#")
            ):
                continue

            # Get the full URL
            full_url = response.urljoin(href)
            parsed_href = urlparse(full_url)

            # Ensure the href is within the allowed domain
            if parsed_href.netloc and parsed_href.netloc != "informatics.tuwien.ac.at":
                continue

            # Ignore /news/* links
            if "/news/" in parsed_href.path:
                continue

            # Ignore event calendar links
            if "event-calendar" in parsed_href.path or "calendar" in parsed_href.path:
                continue

            # TODO: Ignore https://informatics.tuwien.ac.at/people/all
            if "/people/all" in parsed_href.path:
                continue

            yield response.follow(href, self.parse_item)

    def parse(self, response):
        """Override the default parse method to use parse_item for all pages."""
        return self.parse_item(response)


class TUWienSpider(CrawlSpider):
    """Spider for tuwien.at website with focus on study information."""

    name = "tuwien_spider"
    allowed_domains = ["tuwien.at", "www.tuwien.at"]
    start_urls = ["https://tuwien.at/studium", "https://www.tuwien.at/en/studies"]

    rules = (
        Rule(
            LinkExtractor(allow=(r"/studium/.*", r"/en/studies/.*")),
            callback="parse_item",
            follow=True,
        ),
    )

    def __init__(self, output_dir: str = "knowledge_base/tuwienat", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def parse_item(self, response):
        """Parse individual pages with TUWien-specific logic."""
        self.logger.info(f"Scraping: {response.url}")

        # Extract main content with TUWien-specific selector
        main_content_html = response.css("main#content").get()

        if not main_content_html:
            self.logger.warning(f"Could not find main content for {response.url}")
            return

        # Convert to markdown with metadata
        markdown_content = md(main_content_html, heading_style="ATX")
        source_url = response.url
        markdown_content = f"<!-- Source URL: {source_url} -->\n\n{markdown_content}"

        # Apply content cleaning (remove data images)
        markdown_content = remove_data_images(markdown_content)

        # Save content
        parsed_url = urlparse(response.url)
        filename = sanitize_filename(parsed_url.path) + ".md"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        self.logger.info(f"  -> Saved to {filepath}")

        # Follow links with TUWien-specific filtering
        for href in response.css("a::attr(href)").getall():
            # Ignore specific URL types
            if href.startswith("tel:") or href.startswith("javascript:"):
                continue

            # Get full URL and parse
            full_url = response.urljoin(href)
            parsed_href = urlparse(full_url)

            # Restrict to specific subpaths only
            if not parsed_href.path.startswith(
                "/studium"
            ) and not parsed_href.path.startswith("/en/studies"):
                continue

            # Ignore event pages
            if parsed_href.path.startswith(
                "/en/studies/student-support/events/"
            ) or parsed_href.path.startswith(
                "/studium/student-support/veranstaltungen/"
            ):
                continue

            # Ignore news pages
            if parsed_href.path.startswith(
                "/studium/news/"
            ) or parsed_href.path.startswith("/en/studies/news/"):
                continue

            # Ignore event calendars
            if (
                "event-calendar" in parsed_href.path
                or "eventkalender" in parsed_href.path
            ):
                continue

            # TODO: Ignore blog pages
            # *studieren-im-ausland_blogs*.md
            # *studying-abroad_blogs*.md
            if "blogs" in parsed_href.path and (
                "studieren-im-ausland" in parsed_href.path
                or "studying-abroad" in parsed_href.path
            ):
                continue

            yield response.follow(href, self.parse_item)

    def parse(self, response):
        """Override the default parse method to use parse_item for all pages."""
        return self.parse_item(response)


class VOWiFSINFSpider(CrawlSpider):
    """Spider for vowi.fsinf.at website with caching support."""

    name = "vowi_spider"
    allowed_domains = ["vowi.fsinf.at"]
    start_urls = ["https://vowi.fsinf.at"]

    rules = (
        Rule(
            LinkExtractor(allow=(r".*",), deny=(r"/news/.*",)),  # Exclude news links
            callback="parse_item",
            follow=True,
        ),
    )

    def __init__(self, output_dir: str = "knowledge_base/vowifsinf", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def make_requests_from_url(self, url):
        """Override to check for cached files before making requests."""
        # Check if we already have this URL cached
        parsed_url = urlparse(url)
        sanitized_path = sanitize_filename(parsed_url.path)
        url_hash = generate_filename_hash(url)
        base_filename = f"{sanitized_path}_{url_hash}"
        html_filename = base_filename + ".html"
        html_fpath = os.path.join(self.output_dir, html_filename)

        if os.path.exists(html_fpath):
            self.logger.info(f"Using cached file, skipping download: {url}")
            # Create a fake response from cached content
            try:
                with open(html_fpath, "r", encoding="utf-8") as f:
                    cached_html = f.read()
                from scrapy.http import TextResponse

                return [TextResponse(url=url, body=cached_html, encoding="utf-8")]
            except Exception as e:
                self.logger.warning(f"Could not load cached file {html_fpath}: {e}")
                # Fall back to normal request
                pass

        # Normal request if no cache or cache failed
        return super().make_requests_from_url(url)

    def parse_item(self, response):
        """Parse individual pages with VoWi-specific logic and caching."""
        self.logger.info(f"Processing: {response.url}")

        # Check content type to handle different file types (for non-cached responses)
        content_type = response.headers.get("Content-Type", b"").decode("utf-8").lower()
        parsed_url = urlparse(response.url)

        # Skip PDF files (do not download them)
        if "application/pdf" in content_type or parsed_url.path.lower().endswith(
            ".pdf"
        ):
            self.logger.info(f"Skipping PDF: {response.url}")
            return  # Don't process PDFs at all

        # Skip other non-HTML file types (for non-cached responses)
        if (
            content_type  # Only check if content_type is not empty
            and "text/html" not in content_type
            and "application/xhtml" not in content_type
            and not content_type.startswith("text/")
        ):
            self.logger.info(
                f"Skipping non-HTML file: {response.url} (Content-Type: {content_type})"
            )
            return

        # Generate filename with hash to avoid collisions
        sanitized_path = sanitize_filename(parsed_url.path)
        url_hash = generate_filename_hash(response.url)
        base_filename = f"{sanitized_path}_{url_hash}"

        html_filename = base_filename + ".html"
        md_filename = base_filename + ".md"
        html_fpath = os.path.join(self.output_dir, html_filename)
        md_fpath = os.path.join(self.output_dir, md_filename)

        # Save the full HTML content if it's a fresh download (not from cache)
        if not os.path.exists(html_fpath):
            with open(html_fpath, "w", encoding="utf-8") as f:
                f.write(response.text)
            self.logger.info(f"  -> Saved HTML to {html_fpath}")

        # Extract the main content using multiple CSS selectors
        try:
            main_content_html = (
                response.css("main#main").get()
                or response.css("main#content").get()
                or response.css("main").get()
                or response.css("#content").get()
                or response.css(".content").get()
                or response.css("article").get()
            )
        except Exception as e:
            self.logger.warning(f"Could not parse CSS for {response.url}: {e}")
            return

        if not main_content_html:
            self.logger.warning(f"Could not find main content for {response.url}")
            return

        # Convert to markdown with metadata
        markdown_content = md(main_content_html, heading_style="ATX")
        source_url = response.url
        markdown_content = f"<!-- Source URL: {source_url} -->\n\n{markdown_content}"

        # Apply content cleaning (remove data images)
        markdown_content = remove_data_images(markdown_content)

        # Save markdown content
        with open(md_fpath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        self.logger.info(f"  -> Saved to {md_fpath}")

        # Follow links with minimal filtering
        for href in response.css("a::attr(href)").getall():
            # Ignore specific URL types
            if (
                href.startswith("tel:")
                or href.startswith("javascript:")
                or href.startswith("mailto:")
                or href.startswith("#")
            ):
                continue

            # Get the full URL
            full_url = response.urljoin(href)
            parsed_href = urlparse(full_url)

            # Ensure the href is within the allowed domain
            if parsed_href.netloc and parsed_href.netloc != "vowi.fsinf.at":
                continue

            # Exclude news links (already in rules, but double-check)
            if "/news/" in parsed_href.path:
                continue

            yield response.follow(href, self.parse_item)

    def parse(self, response):
        """Override the default parse method to use parse_item for all pages."""
        return self.parse_item(response)


class WINFATSpider(Spider):
    """Spider for winf.at website with specific content selector."""

    name = "winf_spider"
    allowed_domains = ["winf.at"]
    start_urls = ["https://winf.at"]

    def __init__(self, output_dir: str = "knowledge_base/winfat", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger.info(f"Saving markdown files to: {self.output_dir}")

    def parse(self, response):
        """Parse pages and follow links with WINF-specific logic."""
        self.logger.info(f"Scraping: {response.url}")

        # Extract the main content using WINF-specific CSS selector
        main_content_html = response.css("main#brx-content").get()

        if not main_content_html:
            self.logger.warning(f"Could not find main content for {response.url}")
            return

        # Convert to markdown with metadata
        markdown_content = md(main_content_html, heading_style="ATX")
        source_url = response.url
        markdown_content = f"<!-- Source URL: {source_url} -->\n\n{markdown_content}"

        # Apply content cleaning (remove data images)
        markdown_content = remove_data_images(markdown_content)

        # Save content
        parsed_url = urlparse(response.url)
        filename = sanitize_filename(parsed_url.path) + ".md"
        filepath = os.path.join(self.output_dir, filename)

        # Save the Markdown content to a file with error handling
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            self.logger.info(f"  -> Saved to {filepath}")
        except IOError as e:
            self.logger.error(f"Error saving file {filepath}: {e}")

        # Follow all links within the same domain with filtering
        for href in response.css("a::attr(href)").getall():
            if (
                href.startswith("tel:")
                or href.startswith("javascript:")
                or href.startswith("mailto:")
                or href.startswith("#")
            ):
                continue
            yield response.follow(href, self.parse)


# Scraper classes that use the spiders
class HTUATScraper(BaseScraper):
    """Scraper for htu.at website."""

    def __init__(self, output_dir: str = "knowledge_base/htuat"):
        super().__init__("https://htu.at/", output_dir)

    def run(self) -> None:
        """Run the HTU scraper with proper settings."""
        process = CrawlerProcess(
            {
                "USER_AGENT": "WinfBeratung Scraper/1.0 (+http://winf.at/kontakt/)",
                "ROBOTSTXT_OBEY": True,
                "CONCURRENT_REQUESTS": 16,
                "LOG_LEVEL": "INFO",
                "DOWNLOAD_DELAY": 1.0,
            }
        )

        process.crawl(HTUATSpider, output_dir=str(self.output_dir))
        process.start()


class InformaticsTUWienScraper(BaseScraper):
    """Scraper for informatics.tuwien.ac.at website."""

    def __init__(self, output_dir: str = "knowledge_base/informaticstuwienacat"):
        super().__init__("https://informatics.tuwien.ac.at", output_dir)

    def run(self) -> None:
        """Run the Informatics scraper with proper settings."""
        process = CrawlerProcess(
            {
                "USER_AGENT": "WinfBeratung Scraper/1.0 (+http://winf.at/kontakt/)",
                "ROBOTSTXT_OBEY": True,
                "CONCURRENT_REQUESTS": 16,
                "LOG_LEVEL": "INFO",
                "DOWNLOAD_DELAY": 1.0,
            }
        )

        process.crawl(InformaticsTUWienSpider, output_dir=str(self.output_dir))
        process.start()


class TUWienScraper(BaseScraper):
    """Scraper for tuwien.at website."""

    def __init__(self, output_dir: str = "knowledge_base/tuwienat"):
        super().__init__("https://www.tuwien.at", output_dir)

    def run(self) -> None:
        """Run the TUWien scraper with proper settings."""
        process = CrawlerProcess(
            {
                "USER_AGENT": "WinfBeratung Scraper/1.0 (+http://winf.at/kontakt/)",
                "ROBOTSTXT_OBEY": True,
                "CONCURRENT_REQUESTS": 16,
                "LOG_LEVEL": "INFO",
                "DOWNLOAD_DELAY": 1.0,
            }
        )

        process.crawl(TUWienSpider, output_dir=str(self.output_dir))
        process.start()


class VOWiFSINFScraper(BaseScraper):
    """Scraper for vowi.fsinf.at website."""

    def __init__(self, output_dir: str = "knowledge_base/vowifsinf"):
        super().__init__("https://vowi.fsinf.at", output_dir)

    def run(self) -> None:
        """Run the VoWi scraper with proper settings."""
        process = CrawlerProcess(
            {
                "USER_AGENT": "WinfBeratung Scraper/1.0 (+http://winf.at/kontakt/)",
                "ROBOTSTXT_OBEY": True,
                "CONCURRENT_REQUESTS": 16,
                "LOG_LEVEL": "INFO",
                "DOWNLOAD_DELAY": 1.0,
            }
        )

        process.crawl(VOWiFSINFSpider, output_dir=str(self.output_dir))
        process.start()


class WINFATScraper(BaseScraper):
    """Scraper for winf.at website."""

    def __init__(self, output_dir: str = "knowledge_base/winfat"):
        super().__init__("https://winf.at", output_dir)

    def run(self) -> None:
        """Run the WINF scraper with proper settings."""
        process = CrawlerProcess(
            {
                "USER_AGENT": "WinfBeratung Scraper/1.0 (+http://winf.at/kontakt/)",
                "ROBOTSTXT_OBEY": True,
                "CONCURRENT_REQUESTS": 16,
                "LOG_LEVEL": "INFO",
                "DOWNLOAD_DELAY": 1.0,
            }
        )

        process.crawl(WINFATSpider, output_dir=str(self.output_dir))
        process.start()
