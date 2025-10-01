"""
Tests for RAG pipeline functionality.
"""

from unittest.mock import MagicMock, patch

from freescout_llm.rag_pipeline import RAGPipeline
from freescout_llm.tools.url_summarization import create_url_summarization_tool


class TestRAGPipeline:
    """Test cases for RAG pipeline functionality."""

    @patch("freescout_llm.database_utils.os.path.exists")
    def test_pipeline_initialization_without_db(self, mock_exists):
        """Test pipeline initialization in development mode."""
        mock_exists.return_value = False

        with (
            patch("langchain_ollama.ChatOllama") as mock_chat,
            patch("langchain_ollama.OllamaEmbeddings") as mock_embeddings,
        ):

            mock_chat.return_value = MagicMock()
            mock_embeddings.return_value = MagicMock()

            pipeline = RAGPipeline()

            # In dev mode, vector_db should be None but pipeline should still be ready
            assert pipeline.vector_db is None
            assert pipeline.email_repository_db is None
            assert pipeline.is_ready()

    @patch("freescout_llm.tools.url_summarization.requests.get")
    def test_url_summarization_tool_with_markdown(self, mock_get):
        """Test URL summarization tool with markdownify conversion."""

        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.content = b"""
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Welcome to Test University</h1>
                <p>This page contains information about <strong>course registration</strong>.</p>
                <ul>
                    <li>Students must register by December 15th</li>
                    <li>Registration opens on November 1st</li>
                </ul>
                <script>console.log('test');</script>
            </body>
        </html>
        """
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock LLM response for summarization
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(
            content="Diese Seite bietet Informationen zur Kursanmeldung an der Test University. Studierende müssen sich bis zum 15. Dezember anmelden."
        )

        # Create URL tool directly
        url_tool = create_url_summarization_tool(mock_llm_instance)

        # Test with allowed domain
        result = url_tool.invoke(
            {
                "url": "https://tuwien.at/test",
                "reason": "Check course registration information",
            }
        )

        # Verify the result contains expected information
        assert "https://tuwien.at/test" in result
        assert "Kursanmeldung" in result
        assert "Webseite" in result

    def test_url_tool_domain_whitelist(self):
        """Test URL tool domain whitelisting."""
        mock_llm_instance = MagicMock()
        url_tool = create_url_summarization_tool(mock_llm_instance)

        # Test blocked domain
        result = url_tool.invoke(
            {"url": "https://evil-site.com/malware", "reason": "Test blocked domain"}
        )

        assert "Error: URL domain not allowed" in result
        assert "tuwien.at" in result  # Should mention allowed domains

    @patch("freescout_llm.tools.url_summarization.requests.get")
    def test_url_tool_tiss_support(self, mock_get):
        """Test URL tool TISS domain support with dynamic token authentication."""
        # Mock the HTTP response for TISS
        mock_response = MagicMock()
        mock_response.content = b"""
        <html>
            <head><title>TISS - Course Information</title></head>
            <body>
                <h1>Informatik Studium</h1>
                <p>Informationen zur <strong>Informatik</strong> an der TU Wien.</p>
                <div class="course-info">
                    <h2>Vorlesungsverzeichnis</h2>
                    <p>Anmeldung erforderlich</p>
                </div>
            </body>
        </html>
        """
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock LLM response for summarization
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(
            content="Diese TISS-Seite enthält Informationen zum Informatik-Studium an der TU Wien mit Details zur Vorlesungsanmeldung."
        )

        # Create URL tool directly
        url_tool = create_url_summarization_tool(mock_llm_instance)

        # Test with TISS URL
        result = url_tool.invoke(
            {
                "url": "https://tiss.tuwien.ac.at/course/courseOverview.xhtml?courseNr=123456",
                "reason": "Check course information",
            }
        )

        # Verify the result contains expected information
        assert "https://tiss.tuwien.ac.at" in result
        assert "TISS-Seite" in result
        assert "Informatik" in result

        # Verify that requests.get was called with TISS-specific authentication
        mock_get.assert_called_once()
        call_args = mock_get.call_args

        # Check that the URL was modified to include dsrid token
        called_url = call_args.args[0]
        assert "dsrid=" in called_url
        assert "courseNr=123456" in called_url

        # Check that dynamic cookies were passed (including the token-based cookie)
        assert "cookies" in call_args.kwargs
        cookies = call_args.kwargs["cookies"]
        assert cookies["TISS_LANG"] == "de"
        assert cookies["SERVERID"] == "eps1"

        # Verify that a dynamic dsrwid cookie was created
        dsrwid_cookies = [k for k in cookies.keys() if k.startswith("dsrwid-")]
        assert len(dsrwid_cookies) == 1
        assert cookies[dsrwid_cookies[0]] == "2705"

        # Check that TISS headers were used
        assert "headers" in call_args.kwargs
        headers = call_args.kwargs["headers"]
        assert "sec-ch-ua" in headers
        assert "Chrome" in headers["User-Agent"]

    @patch("freescout_llm.tools.url_summarization.requests.get")
    def test_url_tool_pdf_support(self, mock_get):
        """Test URL tool PDF support."""

        # Mock PDF response
        mock_response = MagicMock()
        mock_response.content = (
            b"Mock PDF content"  # In real test, this would be actual PDF bytes
        )
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch(
            "freescout_llm.tools.url_summarization.pypdf.PdfReader"
        ) as mock_pdf_reader:

            # Mock PDF text extraction
            mock_page = MagicMock()
            mock_page.extract_text.return_value = (
                "This is extracted PDF text about course requirements."
            )
            mock_pdf_instance = MagicMock()
            mock_pdf_instance.pages = [mock_page]
            mock_pdf_reader.return_value = mock_pdf_instance

            # Mock LLM response
            mock_llm_instance = MagicMock()
            mock_llm_instance.invoke.return_value = MagicMock(
                content="Dieses PDF enthält Informationen zu Kursanforderungen."
            )

            url_tool = create_url_summarization_tool(mock_llm_instance)

            result = url_tool.invoke(
                {
                    "url": "https://tuwien.at/document.pdf",
                    "reason": "Check course requirements",
                }
            )

            assert "https://tuwien.at/document.pdf" in result
            assert "PDF" in result
            assert "Kursanforderungen" in result

    @patch("freescout_llm.tools.url_summarization.requests.get")
    def test_url_tool_handles_request_errors(self, mock_get):
        """Test URL tool error handling for network issues."""
        mock_get.side_effect = Exception("Network error")

        mock_llm_instance = MagicMock()
        url_tool = create_url_summarization_tool(mock_llm_instance)

        result = url_tool.invoke(
            {"url": "https://tuwien.at/invalid-page", "reason": "Test error handling"}
        )

        assert "Fehler" in result
        assert "https://tuwien.at/invalid-page" in result

    @patch("freescout_llm.database_utils.os.path.exists")
    def test_tool_creation_and_registration(self, mock_exists):
        """Test that all tools are properly created and registered."""
        mock_exists.return_value = False

        with (
            patch("langchain_ollama.ChatOllama") as mock_chat,
            patch("langchain_ollama.OllamaEmbeddings") as mock_embeddings,
            patch("freescout_llm.rag_pipeline.create_tool_calling_agent") as mock_agent,
            patch("freescout_llm.rag_pipeline.AgentExecutor") as mock_executor,
        ):

            mock_chat.return_value = MagicMock()
            mock_embeddings.return_value = MagicMock()
            mock_agent.return_value = MagicMock()
            mock_executor.return_value = MagicMock()

            pipeline = RAGPipeline()

            # Verify pipeline is properly initialized
            assert pipeline.is_ready()

            # Verify that create_tool_calling_agent was called with tools
            mock_agent.assert_called_once()
            args = mock_agent.call_args[0]
            tools = args[1]  # Second argument should be the tools list

            # Should have 3 tools: search_knowledge_base, search_past_cases, fetch_and_summarize_url
            assert len(tools) == 3

            # Check tool names
            tool_names = [tool.name for tool in tools]
            assert "search_knowledge_base" in tool_names
            assert "search_past_cases" in tool_names
            assert "fetch_and_summarize_url" in tool_names
