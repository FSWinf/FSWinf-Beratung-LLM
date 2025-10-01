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

    def test_numbered_list_without_blank_line(self):
        """Test that numbered lists work without requiring blank lines before them."""
        # This was the main issue we fixed - lists should work without blank lines
        test_cases = [
            # Case 1: List immediately after text
            {
                "input": "Lorem Ipsum\n1. First item\n2. Second item",
                "expected_tags": [
                    "<ol>",
                    "<li>First item</li>",
                    "<li>Second item</li>",
                ],
            },
            # Case 2: Bulleted list after text
            {
                "input": "Some text\n- First bullet\n- Second bullet",
                "expected_tags": [
                    "<ul>",
                    "<li>First bullet</li>",
                    "<li>Second bullet</li>",
                ],
            },
            # Case 3: List after bold text
            {
                "input": "**Important:**\n1. First step\n2. Second step",
                "expected_tags": [
                    "<strong>Important:</strong>",
                    "<ol>",
                    "<li>First step</li>",
                ],
            },
        ]

        for case in test_cases:
            result = markdown_to_html(case["input"])
            for expected_tag in case["expected_tags"]:
                assert (
                    expected_tag in result
                ), f"Expected '{expected_tag}' in result for input: {case['input']}"

    def test_numbered_list_with_blank_line(self):
        """Test that numbered lists still work with blank lines (standard markdown)."""
        markdown_content = "Text before\n\n1. First item\n2. Second item"
        result = markdown_to_html(markdown_content)

        # Should still produce proper list HTML
        assert "<ol>" in result
        assert "<li>First item</li>" in result
        assert "<li>Second item</li>" in result
