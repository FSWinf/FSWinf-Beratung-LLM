"""
Tests for vector database generation functionality.
"""

from unittest.mock import MagicMock, patch

from freescout_llm.database import (
    EmailChainProcessor,
    KnowledgeBaseProcessor,
    VectorDatabaseManager,
)
from freescout_llm.vector_db import VectorDatabaseGenerator


class TestVectorDatabaseGeneration:
    """Test cases for vector database generation."""

    @patch("freescout_llm.database.document_loaders.load_documents")
    @patch(
        "freescout_llm.database.vector_db_manager.VectorDatabaseManager.initialize_embeddings"
    )
    def test_knowledge_base_generation(self, mock_init_embeddings, mock_load_docs):
        """Test knowledge base vector database generation."""
        mock_init_embeddings.return_value = True
        mock_load_docs.return_value = []  # Empty documents for simple test

        generator = VectorDatabaseGenerator()
        result = generator.generate(force=True)

        # Should handle empty documents gracefully
        assert result is False  # No documents to process
        mock_init_embeddings.assert_called_once()
        mock_load_docs.assert_called_once()

    @patch("freescout_llm.database.document_loaders.load_email_chains")
    @patch(
        "freescout_llm.database.vector_db_manager.VectorDatabaseManager.initialize_embeddings"
    )
    def test_email_repository_generation(self, mock_init_embeddings, mock_load_emails):
        """Test email repository generation."""
        mock_init_embeddings.return_value = True
        mock_load_emails.return_value = []  # Empty documents for simple test

        generator = VectorDatabaseGenerator()
        result = generator.generate_email_repository(force=True)

        # Should handle empty documents gracefully
        assert result is True  # Empty case returns True
        mock_init_embeddings.assert_called_once()
        mock_load_emails.assert_called_once()

    def test_knowledge_base_processor(self):
        """Test knowledge base document processing."""
        from langchain.schema import Document

        processor = KnowledgeBaseProcessor()

        # Test document with source URL in content
        doc = Document(
            page_content="<!-- Source URL: https://example.com -->\n\nContent here",
            metadata={"source": "/path/to/file.md"},
        )

        processed_doc = processor.process_metadata(doc)

        assert processed_doc.metadata["source_url"] == "https://example.com"
        assert "<!-- Source URL:" not in processed_doc.page_content

    def test_email_chain_processor(self):
        """Test email chain document processing."""
        from langchain.schema import Document

        processor = EmailChainProcessor()

        # Test email document with metadata in content
        content = """Subject: Test Email
Date: 2024-01-01
Case Type: Course Registration
Tags: urgent, deadline
---
Email content here"""

        doc = Document(page_content=content, metadata={"source": "/path/to/email.md"})
        processed_doc = processor.process_metadata(doc)

        assert processed_doc.metadata["email_subject"] == "Test Email"
        assert processed_doc.metadata["email_date"] == "2024-01-01"
        assert processed_doc.metadata["case_type"] == "Course Registration"
        assert processed_doc.metadata["document_type"] == "email_chain"
        assert processed_doc.page_content == "Email content here"

    @patch("freescout_llm.database.vector_db_manager.initialize_embeddings")
    def test_vector_db_manager_initialization(self, mock_init_embeddings):
        """Test vector database manager initialization."""
        mock_init_embeddings.return_value = MagicMock()

        manager = VectorDatabaseManager()
        result = manager.initialize_embeddings()

        assert result is True
        mock_init_embeddings.assert_called_once()

    def test_document_splitting(self):
        """Test document splitting functionality."""
        from langchain.schema import Document

        processor = KnowledgeBaseProcessor()

        # Create a long document that should be split
        long_content = "This is a test document. " * 100  # Make it long enough to split
        doc = Document(page_content=long_content, metadata={"source": "test.md"})

        processed_docs = processor.process_documents([doc])

        # Should have multiple chunks
        assert len(processed_docs) > 1

        # All chunks should have the same source metadata
        for chunk in processed_docs:
            assert chunk.metadata["source"] == "test.md"


class TestCommandLineInterface:
    """Test command line interface functions."""

    @patch("freescout_llm.vector_db.VectorDatabaseGenerator.generate")
    def test_generate_vector_db_command(self, mock_generate):
        """Test the command line interface for vector DB generation."""
        from freescout_llm.vector_db import generate_vector_db_command

        mock_generate.return_value = True

        result = generate_vector_db_command(force=True)

        assert result is True
        mock_generate.assert_called_once_with(force=True)

    @patch("freescout_llm.vector_db.VectorDatabaseGenerator.generate_email_repository")
    def test_generate_email_repository_command(self, mock_generate_email):
        """Test the command line interface for email repository generation."""
        from freescout_llm.vector_db import generate_email_repository_command

        mock_generate_email.return_value = True

        result = generate_email_repository_command(force=True)

        assert result is True
        mock_generate_email.assert_called_once_with(
            email_chains_dir="./email_chains/", force=True
        )

    @patch("freescout_llm.vector_db.VectorDatabaseGenerator.generate")
    @patch("freescout_llm.vector_db.VectorDatabaseGenerator.generate_email_repository")
    def test_generate_all_databases(self, mock_generate_email, mock_generate_kb):
        """Test generating all databases at once."""
        from freescout_llm.vector_db import generate_all_databases

        mock_generate_kb.return_value = True
        mock_generate_email.return_value = True

        result = generate_all_databases(force=True)

        assert result is True
        mock_generate_kb.assert_called_once_with(force=True)
        mock_generate_email.assert_called_once_with(force=True)
