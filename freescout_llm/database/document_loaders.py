"""
Document loading utilities for vector database generation.
Handles loading of different document types from the file system.
"""

import json
import os
from typing import List

from langchain.schema import Document
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFDirectoryLoader,
    TextLoader,
)


def load_pdf_metadata(pdf_path: str) -> dict:
    """
    Load metadata for a PDF file from its associated JSON file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary containing PDF metadata, or empty dict if no metadata found
    """
    # Get the corresponding JSON metadata file
    json_path = pdf_path.rsplit(".", 1)[0] + ".json"

    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                return metadata
        except Exception as e:
            print(f"Warning: Could not load PDF metadata from {json_path}: {e}")

    return {}


class PDFLoaderWithMetadata(PyPDFDirectoryLoader):
    """Custom PDF loader that includes metadata from JSON files."""

    def load(self) -> List[Document]:
        """Load PDFs and enrich them with metadata from JSON files."""
        # Load PDFs normally first
        docs = super().load()

        # Enrich each document with metadata from JSON files
        enriched_docs = []
        for doc in docs:
            # Get the PDF file path from the document metadata
            pdf_path = doc.metadata.get("source", "")

            if pdf_path:
                # Load additional metadata from JSON file
                pdf_metadata = load_pdf_metadata(pdf_path)

                # Merge the metadata
                enriched_metadata = {**doc.metadata, **pdf_metadata}

                # Create new document with enriched metadata
                enriched_doc = Document(
                    page_content=doc.page_content, metadata=enriched_metadata
                )
                enriched_docs.append(enriched_doc)
            else:
                # Keep original document if no source path
                enriched_docs.append(doc)

        return enriched_docs


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

    # Load PDF files with metadata enrichment
    pdf_loader = PDFLoaderWithMetadata(knowledge_base_dir, glob="**/*.pdf")
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
