#!/usr/bin/env python3
"""
Vector Database Generation Module

This module generates a SQLite vector database from the knowledge base documents.
It should be run whenever the knowledge base is updated.
"""

from .database import (
    EmailChainProcessor,
    KnowledgeBaseProcessor,
    VectorDatabaseManager,
    load_documents,
    load_email_chains,
)


class VectorDatabaseGenerator:
    """Handles generation of vector databases from knowledge base documents and email repositories."""

    def __init__(self, knowledge_base_dir: str = "./knowledge_base/"):
        """
        Initialize the vector database generator.

        Args:
            knowledge_base_dir: Directory containing knowledge base documents
        """
        self.knowledge_base_dir = knowledge_base_dir
        self.db_manager = VectorDatabaseManager()
        self.kb_processor = KnowledgeBaseProcessor()
        self.email_processor = EmailChainProcessor()

    def generate(self, force: bool = False) -> bool:
        """
        Generate a vector database from the knowledge base documents.

        Args:
            force: If True, regenerates the database even if it's up to date.

        Returns:
            True if successful, False otherwise.
        """
        print("Starting knowledge base vector database generation...")

        # Initialize embeddings
        if not self.db_manager.initialize_embeddings():
            return False

        # Check if we need to regenerate the database
        if not force:
            print("Vector database generation requested. Checking for new files...")
        else:
            print("Creating new vector database...")

        try:
            # Load and process knowledge base documents
            docs = load_documents(self.knowledge_base_dir)
            if not docs:
                return False

            # Process documents (metadata extraction and splitting)
            processed_docs = self.kb_processor.process_documents(docs)

            # Generate the database
            return self.db_manager.generate_database(
                table_name="rag",
                documents=processed_docs,
                force=force,
                table_type="knowledge base",
            )

        except Exception as e:
            print(f"Error generating vector database: {e}")
            return False

    def generate_email_repository(
        self, email_chains_dir: str = "./email_chains/", force: bool = False
    ) -> bool:
        """
        Generate or update the email repository table in the vector database.

        Args:
            email_chains_dir: Directory containing email chain documents
            force: If True, regenerates the repository even if it exists

        Returns:
            True if successful, False otherwise
        """
        print("Starting email repository generation...")

        # Initialize embeddings
        if not self.db_manager.initialize_embeddings():
            return False

        try:
            # Load and process email chain documents
            email_docs = load_email_chains(email_chains_dir)
            if not email_docs:
                print("No email chain documents to process.")
                return True

            # Process email documents (metadata extraction and splitting)
            processed_docs = self.email_processor.process_documents(email_docs)

            # Generate the email repository database
            return self.db_manager.generate_database(
                table_name="email_repository",
                documents=processed_docs,
                force=force,
                table_type="email chain",
            )

        except Exception as e:
            print(f"Error generating email repository: {e}")
            return False


# Command line interface functions
def generate_vector_db_command(force: bool = False) -> bool:
    """Command line interface for generating vector database."""
    generator = VectorDatabaseGenerator()
    return generator.generate(force=force)


def generate_email_repository_command(
    email_chains_dir: str = "./email_chains/", force: bool = False
) -> bool:
    """Command line interface for generating email repository."""
    generator = VectorDatabaseGenerator()
    return generator.generate_email_repository(
        email_chains_dir=email_chains_dir, force=force
    )


def generate_all_databases(force: bool = False) -> bool:
    """Generate both knowledge base and email repository databases."""
    generator = VectorDatabaseGenerator()

    print("=== Generating Knowledge Base Database ===")
    kb_success = generator.generate(force=force)

    print("\n=== Generating Email Repository Database ===")
    email_success = generator.generate_email_repository(force=force)

    return kb_success and email_success
