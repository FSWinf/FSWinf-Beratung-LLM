"""
Document processors for different types of content.
Handles metadata extraction and content processing.
"""

import random
from abc import ABC, abstractmethod
from typing import List

from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm


class DocumentProcessor(ABC):
    """Abstract base class for document processors."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the document processor.

        Args:
            chunk_size: Maximum size of each document chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    def process_documents(self, docs: List[Document]) -> List[Document]:
        """
        Process a list of documents: extract metadata and split into chunks.

        Args:
            docs: List of documents to process

        Returns:
            List of processed and split document chunks
        """
        if not docs:
            return []

        # Process metadata for each document
        print("Processing document metadata...")
        processed_docs = []
        for doc in tqdm(docs, desc="Processing metadata", unit="doc"):
            processed_doc = self.process_metadata(doc)
            processed_docs.append(processed_doc)

        # Split the processed documents
        splits = self._split_documents(processed_docs)

        return splits

    @abstractmethod
    def process_metadata(self, doc: Document) -> Document:
        """
        Process document metadata for a specific document type.

        Args:
            doc: Document to process

        Returns:
            Document with processed metadata
        """
        pass

    def _split_documents(self, docs: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        print("Splitting documents into chunks...")

        splits = []
        for doc in tqdm(docs, desc="Splitting documents", unit="doc"):
            doc_splits = self.text_splitter.split_documents([doc])
            splits.extend(doc_splits)

        # Randomize order to avoid any ordering bias
        random.shuffle(splits)

        print(f"Created {len(splits)} document chunks.")
        return splits


class KnowledgeBaseProcessor(DocumentProcessor):
    """Processor for knowledge base documents."""

    def process_metadata(self, doc: Document) -> Document:
        """Process knowledge base document metadata to extract source URLs."""
        source_url = (
            doc.metadata.get("source", None) if isinstance(doc.metadata, dict) else None
        )

        content = doc.page_content

        # Extract source URL from content if present
        if content.startswith("<!-- Source URL:"):
            lines = content.split("\n")
            first_line = lines[0]
            if "Source URL:" in first_line:
                start = first_line.find("Source URL:") + len("Source URL:")
                end = first_line.find("-->")
                if end > start:
                    source_url = first_line[start:end].strip()
                    content = "\n".join(lines[2:])

        metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
        metadata = {**metadata, "source_url": source_url}

        return Document(page_content=content, metadata=metadata)


class EmailChainProcessor(DocumentProcessor):
    """Processor for email chain documents."""

    def process_metadata(self, doc: Document) -> Document:
        """Process email chain metadata to include case information."""
        content = doc.page_content
        metadata = doc.metadata if isinstance(doc.metadata, dict) else {}

        # Extract metadata from the content if available
        lines = content.split("\n")
        extracted_metadata = {}
        content_start = 0

        # Look for metadata at the beginning of the document
        for i, line in enumerate(lines):
            if line.startswith("Subject:"):
                extracted_metadata["email_subject"] = line.replace(
                    "Subject:", ""
                ).strip()
            elif line.startswith("Date:"):
                extracted_metadata["email_date"] = line.replace("Date:", "").strip()
            elif line.startswith("Case Type:"):
                extracted_metadata["case_type"] = line.replace("Case Type:", "").strip()
            elif line.startswith("Tags:"):
                extracted_metadata["tags"] = line.replace("Tags:", "").strip()
            elif line.startswith("---") and i > 0:
                content_start = i + 1
                break

        # Clean content by removing metadata header
        if content_start > 0:
            content = "\n".join(lines[content_start:])

        # Merge with existing metadata
        final_metadata = {
            **metadata,
            **extracted_metadata,
            "document_type": "email_chain",
        }

        return Document(page_content=content, metadata=final_metadata)
