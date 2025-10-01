"""
Database package for vector database generation and management.
Contains utilities for knowledge base and email repository databases.
"""

from .document_loaders import load_documents, load_email_chains
from .document_processors import EmailChainProcessor, KnowledgeBaseProcessor
from .vector_db_manager import VectorDatabaseManager

__all__ = [
    "KnowledgeBaseProcessor",
    "EmailChainProcessor",
    "VectorDatabaseManager",
    "load_documents",
    "load_email_chains",
]
