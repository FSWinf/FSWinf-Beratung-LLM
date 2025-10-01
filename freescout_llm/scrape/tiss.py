"""
TISS (TU Wien Information Systems and Services) scraper.
"""

import logging
import random
import re
import time
from collections import deque
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from .base import BaseScraper


class TISSScraper(BaseScraper):
    """
    Scraper for TISS website.

    Handles the complex TISS authentication and token system
    to scrape course and administrative information.
    """

    def __init__(self, output_dir: str = "knowledge_base/tiss"):
        """
        Initialize the TISS scraper.

        Args:
            output_dir: Directory to save scraped content
        """
        super().__init__("https://tiss.tuwien.ac.at", output_dir)

        # Set up logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        # Global queue for URLs to process
        self.url_queue = deque()
        self.processed_urls = set()

        # Initialize session with proper headers and cookies
        self.session = self._setup_session()

    def _setup_session(self) -> requests.Session:
        """
        Set up session with cookies and headers from working configuration.

        Returns:
            Configured requests session
        """
        session = requests.Session()

        # Cookies from working curl command
        session.cookies.update(
            {
                "TISS_LANG": "de",
                "SERVERID": "eps1",
            }
        )

        # Headers from working curl command
        session.headers.update(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
            }
        )

        return session

    def generate_new_request_token(self) -> str:
        """
        Generate a new request token similar to the JavaScript function:
        generateNewRequestToken: function () {
          return '' + Math.floor(999 * Math.random())
        }

        Returns:
            Random token string
        """
        return str(int(999 * random.random()))

    def add_token_to_url(self, url: str, token: str) -> str:
        """
        Add the dsrid token to a URL, similar to the JavaScript setUrlParam function.

        Args:
            url: URL to modify
            token: Token to add

        Returns:
            URL with token parameter
        """
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        query_params["dsrid"] = [token]

        # Convert back to flat dict for urlencode (taking first value of each list)
        flat_params = {k: v[0] for k, v in query_params.items()}

        # Rebuild query string using urlencode
        new_query = urlencode(flat_params)

        # Rebuild URL
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)

    def normalize_url(self, url: str) -> str:
        """
        Normalize a URL by removing the dsrid parameter for comparison purposes.
        This ensures URLs with different dsrid tokens are treated as the same URL.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL without dsrid parameter
        """
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)

        # Remove dsrid parameter if it exists
        if "dsrid" in query_params:
            del query_params["dsrid"]

        # Convert back to flat dict for urlencode (taking first value of each list)
        flat_params = {k: v[0] for k, v in query_params.items()}

        # Rebuild query string using urlencode
        new_query = urlencode(flat_params)

        # Rebuild URL
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)

    def update_session_cookies(self, token: str) -> None:
        """
        Update session cookies with the new token, similar to:
        dswh.utils.storeCookie('dsrwid-' + b, dswh.windowId, 3);

        Args:
            token: Token to store in cookies
        """
        self.session.cookies[f"dsrwid-{token}"] = (
            "2705"  # Using the windowId from existing cookies
        )

    def sanitize_filename(self, text: str) -> str:
        """
        Sanitize text to be used as a filename.

        Args:
            text: Text to sanitize

        Returns:
            Safe filename
        """
        # Remove/replace problematic characters
        text = re.sub(r'[<>:"/\\|?*]', "_", text)
        text = re.sub(r"\s+", "_", text)  # Replace whitespace with underscores
        text = text.strip("_")  # Remove leading/trailing underscores

        # Limit length
        if len(text) > 200:
            text = text[:200]

        return text if text else "unknown"

    def process_url(self, url: str) -> None:
        """
        Process a single URL and save its content.

        Args:
            url: URL to process
        """
        normalized_url = self.normalize_url(url)

        if normalized_url in self.processed_urls:
            self.logger.debug(f"Already processed: {normalized_url}")
            return

        self.logger.info(f"Processing: {url}")

        # Generate new token and update URL
        token = self.generate_new_request_token()
        url_with_token = self.add_token_to_url(url, token)
        self.update_session_cookies(token)

        try:
            response = self.session.get(url_with_token, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract title
            title_elem = soup.find("title")
            title = title_elem.text.strip() if title_elem else "No Title"

            # Extract main content (try different selectors)
            content_selectors = ["#contentInner", ".content", "main", "#main", "body"]

            content_html = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content_html = str(content_elem)
                    break

            if not content_html:
                self.logger.warning(f"No content found for {url}")
                return

            # Convert to markdown
            markdown_content = md(content_html)

            # Create filename from title or URL path
            if title and title != "No Title":
                filename = self.sanitize_filename(title)
            else:
                parsed_url = urlparse(url)
                filename = self.sanitize_filename(parsed_url.path)

            if not filename:
                filename = f"page_{len(self.processed_urls)}"

            # Save content
            self.save_content(
                f"# {title}\n\nSource: {url}\n\n{markdown_content}", filename
            )

            # Extract and queue new URLs
            self._extract_links(soup, url)

            self.processed_urls.add(normalized_url)

        except requests.RequestException as e:
            self.logger.error(f"Error processing {url}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error processing {url}: {e}")

        # Small delay to be respectful
        time.sleep(1)

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> None:
        """
        Extract and queue new links from the page.

        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links
        """
        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Resolve relative URLs
            full_url = urljoin(base_url, href)

            # Only process TISS URLs
            if not full_url.startswith(self.base_url):
                continue

            normalized = self.normalize_url(full_url)

            if normalized not in self.processed_urls:
                self.url_queue.append(full_url)

    def run(self) -> None:
        """
        Run the TISS scraper.
        """
        # Start with the main TISS page
        self.url_queue.append(self.base_url)

        # Add some important starting URLs
        important_urls = [
            f"{self.base_url}/curriculum/public/ue.xhtml?dswid=&dsrid=",
            f"{self.base_url}/education/admissions.xhtml?dswid=&dsrid=",
            f"{self.base_url}/education/curricula.xhtml?dswid=&dsrid=",
        ]

        for url in important_urls:
            self.url_queue.append(url)

        processed_count = 0
        max_pages = 1000  # Limit to prevent infinite crawling

        while self.url_queue and processed_count < max_pages:
            url = self.url_queue.popleft()
            self.process_url(url)
            processed_count += 1

            if processed_count % 50 == 0:
                self.logger.info(
                    f"Processed {processed_count} pages, {len(self.url_queue)} in queue"
                )

        self.logger.info(f"Completed TISS scraping. Processed {processed_count} pages.")
