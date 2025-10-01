"""
FreeScout LLM Integration

A modular system for processing FreeScout conversations and generating
AI-powered email suggestions using Retrieval-Augmented Generation (RAG).

This package provides:
- FreeScout API client for conversation management
- RAG pipeline for AI-powered response generation
- Text processing utilities for format conversion
- Conversation processor for end-to-end workflow
- CLI interface for easy usage

Example usage:
    from freescout_llm import ConversationProcessor

    processor = ConversationProcessor()
    if processor.is_ready():
        success = processor.process_conversation(12345)
"""

from freescout_llm.config import validate_config
from freescout_llm.conversation_processor import ConversationProcessor
from freescout_llm.freescout_api import FreeScoutAPI
from freescout_llm.rag_pipeline import RAGPipeline
from freescout_llm.server import FreeScoutWebhookServer, start_server_command
from freescout_llm.text_processing import (
    extract_text_from_html,
    html_to_markdown,
    markdown_to_html,
)
from freescout_llm.vector_db import VectorDatabaseGenerator, generate_vector_db_command

__version__ = "1.0.0"
__author__ = "FreeScout LLM Integration Team"
__email__ = "admin@example.com"

__all__ = [
    "ConversationProcessor",
    "FreeScoutAPI",
    "RAGPipeline",
    "FreeScoutWebhookServer",
    "VectorDatabaseGenerator",
    "extract_text_from_html",
    "html_to_markdown",
    "markdown_to_html",
    "validate_config",
    "start_server_command",
    "generate_vector_db_command",
]
