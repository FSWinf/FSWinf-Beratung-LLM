"""
URL summarization tool for the RAG pipeline.
Provides web content fetching and summarization capabilities.
"""

import random
from io import BytesIO
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pypdf
import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
from markdownify import markdownify

# Whitelisted domains for security
ALLOWED_DOMAINS = {
    "tuwien.at",
    "winf.at",
    "htu.at",
    "fsinf.at",
    "vowi.fsinf.at",
    "informatics.tuwien.ac.at",
    "tiss.tuwien.ac.at",
}


def _is_domain_allowed(url: str) -> bool:
    """Check if the URL domain is in the whitelist."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]

        return domain in ALLOWED_DOMAINS
    except Exception:
        return False


def _is_tiss_url(url: str) -> bool:
    """Check if the URL is from TISS (tiss.tuwien.ac.at)."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]

        return domain == "tiss.tuwien.ac.at"
    except Exception:
        return False


def _extract_pdf_text(content: bytes) -> str:
    """Extract text from PDF content."""
    try:
        pdf_reader = pypdf.PdfReader(BytesIO(content))

        text_parts = []
        for page in pdf_reader.pages:
            text_parts.append(page.extract_text())

        return "\n".join(text_parts)
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"


def _get_browser_headers() -> dict:
    """Get realistic browser headers for web requests."""
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
        "Accept-Language": "de,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }


def _get_tiss_headers() -> dict:
    """Get TISS-specific headers for accessing tiss.tuwien.ac.at."""
    return {
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


def _get_tiss_cookies() -> dict:
    """Get TISS-specific cookies for accessing tiss.tuwien.ac.at."""
    return {
        "TISS_LANG": "de",
        "SERVERID": "eps1",
    }


def _generate_tiss_token() -> str:
    """
    Generate a new TISS request token similar to the JavaScript function:
    generateNewRequestToken: function () {
      return '' + Math.floor(999 * Math.random())
    }

    Returns:
        Random token string
    """
    return str(int(999 * random.random()))


def _add_tiss_token_to_url(url: str, token: str) -> str:
    """
    Add the dsrid token to a TISS URL, similar to the JavaScript setUrlParam function.

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


def _get_tiss_session_cookies(token: str) -> dict:
    """
    Get TISS session cookies including the dynamic token cookie.

    Args:
        token: The generated token for this request

    Returns:
        Dictionary with all required TISS cookies
    """
    cookies = _get_tiss_cookies()
    # Add the dynamic token cookie similar to: dswh.utils.storeCookie('dsrwid-' + b, dswh.windowId, 3);
    cookies[f"dsrwid-{token}"] = "2705"  # Using the windowId from the TISS scraper
    return cookies


def _process_html_content(content: bytes) -> str:
    """Process HTML content and convert to markdown."""
    soup = BeautifulSoup(content, "html.parser")

    # Remove script, style, nav, header, footer elements
    for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
        element.decompose()

    # Convert HTML to markdown for better structure preservation
    html_content = str(soup)
    text = markdownify(html_content, heading_style="ATX")

    # Clean up the markdown text
    lines = (line.strip() for line in text.splitlines())
    text = "\n".join(line for line in lines if line)

    return text


def _create_summary_prompt(text: str, reason: str) -> str:
    """Create a prompt for summarizing web content."""
    return f"""Bitte erstelle eine präzise Zusammenfassung des folgenden Inhalts von einer Webseite.

Grund für den Abruf dieser Seite: {reason}

Konzentriere dich auf Informationen, die für den angegebenen Grund relevant sind.

Inhalt der Webseite:
{text}

Erstelle eine strukturierte Zusammenfassung auf Deutsch, die folgendes enthält:
1. Hauptthema/Zweck der Seite
2. Wichtige Informationen bezogen auf: {reason}
3. Wichtige Details oder Anforderungen, die erwähnt werden
4. Kontaktinformationen oder nächste Schritte, falls vorhanden

Zusammenfassung:"""


def create_url_summarization_tool(llm):
    """
    Creates a tool that allows the LLM to fetch and summarize web content.

    Args:
        llm: The language model instance for generating summaries

    Returns:
        The URL summarization tool function
    """

    @tool
    def fetch_and_summarize_url(url: str, reason: str = "General information") -> str:
        """
        Fetch content from a URL and provide a summary of the information.
        Only works with whitelisted domains for security.

        Args:
            url: The URL to fetch content from (must be from whitelisted domains)
            reason: The reason for fetching this URL (helps focus the summary)

        Returns:
            String containing a summary of the webpage or PDF content
        """
        try:
            print(f"\n[URL Tool] Fetching content from: {url}")
            print(f"[URL Tool] Reason: {reason}")

            # Validate domain
            if not _is_domain_allowed(url):
                allowed_list = ", ".join(sorted(ALLOWED_DOMAINS))
                return f"Error: URL domain not allowed. Only the following domains are permitted: {allowed_list}"

            # Prepare request parameters based on domain
            if _is_tiss_url(url):
                # Generate token and prepare TISS-specific request
                token = _generate_tiss_token()
                url_with_token = _add_tiss_token_to_url(url, token)
                headers = _get_tiss_headers()
                cookies = _get_tiss_session_cookies(token)
                print(
                    f"[URL Tool] Using TISS-specific headers, cookies, and token: {token}"
                )
                # Use the URL with token for the actual request
                request_url = url_with_token
            else:
                headers = _get_browser_headers()
                cookies = None
                request_url = url

            # Fetch the content
            response = requests.get(
                request_url, headers=headers, cookies=cookies, timeout=15
            )
            response.raise_for_status()

            # Check content type to determine how to process
            content_type = response.headers.get("content-type", "").lower()

            if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                print("[URL Tool] Processing PDF content...")
                text = _extract_pdf_text(response.content)

                if not text.strip():
                    return f"Error: Could not extract readable text from PDF at {url}"

                # Limit PDF text length
                max_length = 6000
                if len(text) > max_length:
                    text = text[:max_length] + "..."

                content_preview = text[:200] + "..." if len(text) > 200 else text
                print(f"[URL Tool] Extracted PDF text preview: {content_preview}")
                content_type_label = "PDF"

            else:
                print("[URL Tool] Processing HTML content...")
                text = _process_html_content(response.content)

                # Limit text length to avoid token limits
                max_length = 5000
                if len(text) > max_length:
                    text = text[:max_length] + "..."
                content_type_label = "Webseite"

            if not text.strip():
                return f"Error: Could not extract readable content from {url}"

            # Create summary using the LLM
            summary_prompt = _create_summary_prompt(text, reason)
            summary_result = llm.invoke(summary_prompt)

            # Extract the summary text
            if hasattr(summary_result, "content"):
                summary = summary_result.content
            else:
                summary = str(summary_result)

            print(f"[URL Tool] Successfully summarized content from {url}")
            return f"URL: {url}\nGrund: {reason}\nInhaltstyp: {content_type_label}\n\nZusammenfassung:\n{summary}"

        except requests.exceptions.RequestException as e:
            error_msg = f"Fehler beim Abrufen der URL {url}: {str(e)}"
            print(f"[URL Tool Error] {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Fehler beim Verarbeiten des Inhalts von {url}: {str(e)}"
            print(f"[URL Tool Error] {error_msg}")
            return error_msg

    return fetch_and_summarize_url
