"""
Text processing utilities for the FreeScout LLM integration.
"""

import bleach
import mistune
from bs4 import BeautifulSoup
from markdownify import markdownify as md


def extract_text_from_html(html_content: str) -> str:
    """
    Extracts plain text from HTML content.

    Args:
        html_content: HTML string to process

    Returns:
        Plain text with newlines as separators
    """
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def html_to_markdown(html_content: str) -> str:
    """
    Converts HTML to markdown format.

    Args:
        html_content: HTML string to convert

    Returns:
        Markdown formatted string
    """
    return md(html_content, heading_style="ATX")


def markdown_to_html(markdown_content: str) -> str:
    """
    Converts markdown to HTML format.

    Args:
        markdown_content: Markdown string to convert

    Returns:
        HTML formatted string
    """
    # Use mistune for more flexible markdown parsing
    # It handles lists without requiring blank lines
    return mistune.html(markdown_content)


def sanitize_html(html_content: str) -> str:
    """
    Sanitizes HTML content to only allow tags necessary for markdown formatting.

    Args:
        html_content: HTML string to sanitize

    Returns:
        Sanitized HTML string with only allowed tags
    """
    # Define allowed tags for basic markdown-equivalent HTML (no code blocks)
    allowed_tags = [
        "p",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "blockquote",
        "a",
        "hr",
        "div",
        "span",
    ]

    # Define allowed attributes
    allowed_attributes = {"a": ["href", "title"], "div": ["class"], "span": ["class"]}

    # Sanitize the HTML
    return bleach.clean(
        html_content, tags=allowed_tags, attributes=allowed_attributes, strip=True
    )
