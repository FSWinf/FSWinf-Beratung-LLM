"""
Document loading utilities for vector database generation.
Handles loading of different document types from the file system.
"""

import os
from typing import List

from langchain.schema import Document
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFDirectoryLoader,
    TextLoader,
)


def load_documents(knowledge_base_dir: str = "./knowledge_base/") -> List[Document]:
    """
    Load documents from the knowledge base directory.

    Args:
        knowledge_base_dir: Directory containing knowledge base documents

    Returns:
        List of loaded documents
    """
    print("Loading documents from knowledge base...")

    # Load markdown files
    loader = DirectoryLoader(
        knowledge_base_dir, glob="**/*.md", loader_cls=TextLoader, show_progress=True
    )
    docs = loader.load()

    # Load PDF files
    pdf_loader = PyPDFDirectoryLoader(knowledge_base_dir, glob="**/*.pdf")
    pdf_docs = pdf_loader.load()
    docs.extend(pdf_docs)

    if not docs:
        print("Warning: No documents found in the knowledge_base directory.")
        return []

    print(f"Loaded {len(docs)} documents.")
    return docs


def load_email_chains(email_chains_dir: str = "./email_chains/") -> List[Document]:
    """
    Load email chain documents from the email repository.

    Args:
        email_chains_dir: Directory containing email chain documents

    Returns:
        List of loaded email chain documents
    """
    print("Loading email chains from repository...")

    if not os.path.exists(email_chains_dir):
        print(f"Email chains directory not found: {email_chains_dir}")
        return []

    loader = DirectoryLoader(
        email_chains_dir, glob="**/*.md", loader_cls=TextLoader, show_progress=True
    )
    docs = loader.load()

    if not docs:
        print("Warning: No email chain documents found.")
        return []

    print(f"Loaded {len(docs)} email chain documents.")
    return docs
