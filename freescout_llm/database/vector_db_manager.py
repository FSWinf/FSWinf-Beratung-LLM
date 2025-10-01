"""
Vector database manager for handling SQLite vector database operations.
Provides a unified interface for creating and managing vector databases.
"""

import json
import os
import sqlite3
from typing import Any, List, Optional, Set

import sqlite_vec
from langchain.schema import Document
from langchain_community.vectorstores import SQLiteVec
from tqdm import tqdm

from ..config import (
    EMBEDDINGS_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_EMBEDDING_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_EMBEDDING_MODEL,
    VECTOR_DB_PATH,
)
from ..llm_providers import initialize_embeddings


class VectorDatabaseManager:
    """Manages vector database operations for knowledge base and email repository."""

    def __init__(self, db_path: str = VECTOR_DB_PATH):
        """
        Initialize the vector database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.embeddings: Optional[Any] = None

    def initialize_embeddings(self) -> bool:
        """Initialize the embeddings model based on the configured provider."""
        print("Initializing embeddings...")

        try:
            if EMBEDDINGS_PROVIDER == "openai":
                if not all([OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_EMBEDDING_MODEL]):
                    print(
                        "Error: OPENAI_API_KEY, OPENAI_BASE_URL, and OPENAI_EMBEDDING_MODEL must be set."
                    )
                    return False

                embeddings_config = {
                    "model": OPENAI_EMBEDDING_MODEL,
                    "base_url": OPENAI_BASE_URL,
                    "api_key": OPENAI_API_KEY,
                }
            else:  # ollama
                if not all([OLLAMA_BASE_URL, OLLAMA_EMBEDDING_MODEL]):
                    print(
                        "Error: OLLAMA_BASE_URL and OLLAMA_EMBEDDING_MODEL must be set."
                    )
                    return False

                embeddings_config = {
                    "model": OLLAMA_EMBEDDING_MODEL,
                    "base_url": OLLAMA_BASE_URL,
                }

            self.embeddings = initialize_embeddings(
                EMBEDDINGS_PROVIDER, **embeddings_config
            )
            print(f"Embeddings initialized using {EMBEDDINGS_PROVIDER} provider.")
            return True

        except ImportError as e:
            provider_name = (
                "langchain-openai"
                if EMBEDDINGS_PROVIDER == "openai"
                else "langchain-ollama"
            )
            print(f"Error: Failed to import {EMBEDDINGS_PROVIDER} embeddings: {e}")
            print(f"Please install the {provider_name} package: uv add {provider_name}")
            return False
        except Exception as e:
            print(f"Error initializing embeddings: {e}")
            return False

    def create_connection(self) -> sqlite3.Connection:
        """Create and configure a SQLite connection with vector extensions."""
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
        connection.enable_load_extension(False)
        return connection

    def create_vector_store(
        self, table_name: str, connection: sqlite3.Connection
    ) -> SQLiteVec:
        """
        Create a vector store for the specified table.

        Args:
            table_name: Name of the table to create
            connection: SQLite database connection

        Returns:
            SQLiteVec instance for the table
        """
        return SQLiteVec(
            table=table_name,
            connection=connection,
            db_file=self.db_path,
            embedding=self.embeddings,
        )

    def get_existing_files(self, table_name: str, force: bool) -> Set[str]:
        """
        Get existing files in the database to avoid duplicates.

        Args:
            table_name: Name of the table to check
            force: If True, return empty set (forces regeneration)

        Returns:
            Set of existing file paths
        """
        existing_files = set()

        if force or not os.path.exists(self.db_path):
            return existing_files

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (table_name,),
            )

            if not cursor.fetchone():
                conn.close()
                return existing_files

            # Try to get sources using JSON extraction first
            try:
                cursor.execute(
                    f"SELECT DISTINCT json_extract(metadata, '$.source') FROM {table_name} "
                    "WHERE json_extract(metadata, '$.source') IS NOT NULL;"
                )
                existing_files = set(row[0] for row in cursor.fetchall() if row[0])
            except sqlite3.OperationalError:
                # Fallback to manual JSON parsing
                cursor.execute(f"SELECT DISTINCT metadata FROM {table_name};")
                for row in cursor.fetchall():
                    try:
                        metadata = json.loads(row[0]) if row[0] else {}
                        source = metadata.get("source")
                        if source:
                            existing_files.add(source)
                    except (json.JSONDecodeError, TypeError):
                        continue

            conn.close()

            if existing_files:
                print(
                    f"Found {len(existing_files)} files already in {table_name} table."
                )

        except Exception as e:
            print(f"Warning: Could not check existing files in {table_name}: {e}")

        return existing_files

    def clear_table(self, table_name: str, connection: sqlite3.Connection) -> None:
        """
        Clear an existing table.

        Args:
            table_name: Name of the table to clear
            connection: SQLite database connection
        """
        print(f"Clearing existing {table_name} table...")
        try:
            cursor = connection.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            connection.commit()
        except Exception as e:
            print(f"Warning: Could not clear {table_name} table: {e}")

    def filter_new_documents(
        self, documents: List[Document], existing_files: Set[str], force: bool
    ) -> List[Document]:
        """
        Filter out documents that already exist in the database.

        Args:
            documents: List of documents to filter
            existing_files: Set of existing file paths
            force: If True, return all documents

        Returns:
            List of new documents to process
        """
        if force or not existing_files:
            return documents

        original_count = len(documents)
        new_documents = [
            doc for doc in documents if doc.metadata.get("source") not in existing_files
        ]

        skipped_count = original_count - len(new_documents)
        if skipped_count > 0:
            print(
                f"Skipping {skipped_count} document chunks that already exist in database."
            )

        return new_documents

    def add_documents_in_batches(
        self,
        vector_store: SQLiteVec,
        documents: List[Document],
        batch_size: int = 5,
        table_type: str = "document",
    ) -> None:
        """
        Add documents to the vector store in batches.

        Args:
            vector_store: Vector store to add documents to
            documents: List of documents to add
            batch_size: Number of documents to process per batch
            table_type: Type of documents being processed (for progress display)
        """
        if not documents:
            print(f"No new {table_type} chunks to process.")
            return

        total_batches = (len(documents) + batch_size - 1) // batch_size

        with tqdm(
            total=len(documents), desc=f"Processing {table_type} chunks", unit="chunk"
        ) as pbar:
            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]
                batch_num = (i // batch_size) + 1

                pbar.set_description(f"Processing batch {batch_num}/{total_batches}")
                vector_store.add_documents(batch)
                pbar.update(len(batch))

    def generate_database(
        self,
        table_name: str,
        documents: List[Document],
        force: bool = False,
        table_type: str = "document",
    ) -> bool:
        """
        Generate or update a vector database table.

        Args:
            table_name: Name of the table to create/update
            documents: List of documents to add
            force: If True, regenerate the table even if it exists
            table_type: Type of documents for progress display

        Returns:
            True if successful, False otherwise
        """
        try:
            if not documents:
                print(f"No {table_type} documents to process.")
                return True

            # Initialize vector database connection
            print(f"Initializing {table_name} database...")
            connection = self.create_connection()
            vector_store = self.create_vector_store(table_name, connection)

            # Clear existing data if force is True
            if force:
                self.clear_table(table_name, connection)
                vector_store.create_table_if_not_exists()

            # Filter out existing documents
            existing_files = self.get_existing_files(table_name, force)
            new_documents = self.filter_new_documents(documents, existing_files, force)

            # Add documents in batches
            self.add_documents_in_batches(
                vector_store, new_documents, table_type=table_type
            )

            print(f"Successfully created and saved {table_name} database.")
            connection.close()
            return True

        except Exception as e:
            print(f"Error generating {table_name} database: {e}")
            if "connection" in locals():
                connection.close()
            return False
