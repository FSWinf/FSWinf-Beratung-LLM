"""
Tests for text processing utilities.
"""

from freescout_llm.text_processing import (
    extract_text_from_html,
    html_to_markdown,
    markdown_to_html,
)


class TestTextProcessing:
    """Test cases for text processing functions."""

    def test_extract_text_from_html(self):
        """Test HTML text extraction."""
        html = "<p>Hello <strong>world</strong>!</p>"
        result = extract_text_from_html(html)
        assert "Hello" in result
        assert "world" in result

    def test_html_to_markdown(self):
        """Test HTML to markdown conversion."""
        html = "<p>Hello <strong>world</strong>!</p>"
        result = html_to_markdown(html)
        assert "**world**" in result or "*world*" in result

    def test_markdown_to_html(self):
        """Test markdown to HTML conversion."""
        markdown = "Hello **world**!"
        result = markdown_to_html(markdown)
        assert "<strong>" in result or "<b>" in result
        assert "world" in result

    def test_round_trip_conversion(self):
        """Test markdown -> HTML -> markdown conversion."""
        original = "# Hello\n\nThis is **bold** text."
        html = markdown_to_html(original)
        back_to_md = html_to_markdown(html)

        # Check that key elements are preserved
        assert "Hello" in back_to_md
        assert "bold" in back_to_md
