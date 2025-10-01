"""
Database utilities for the RAG pipeline.
Handles vector database initialization and connection management.
"""

import os
import sqlite3
from typing import Optional, Tuple

import sqlite_vec
from langchain_community.vectorstores import SQLiteVec


def setup_vector_database(
    db_path: str, embeddings, check_same_thread: bool = False
) -> Tuple[Optional[SQLiteVec], Optional[SQLiteVec]]:
    """
    Set up vector database connections for knowledge base and email repository.

    Args:
        db_path: Path to the SQLite database file
        embeddings: Embeddings instance for vector operations
        check_same_thread: SQLite thread safety setting

    Returns:
        Tuple of (knowledge_db, email_repository_db) or (None, None) if database doesn't exist
    """
    if not os.path.exists(db_path):
        print(f"Warning: Vector database not found at '{db_path}'.")
        print("Running in development mode without vector database.")
        print("The search tools will return mock responses.")
        return None, None

    print("Loading existing vector database...")
    connection = sqlite3.connect(db_path, check_same_thread=check_same_thread)
    connection.row_factory = sqlite3.Row
    connection.enable_load_extension(True)
    sqlite_vec.load(connection)
    connection.enable_load_extension(False)

    # Load knowledge base vector database
    knowledge_db = SQLiteVec(
        table="rag",
        connection=connection,
        db_file=db_path,
        embedding=embeddings,
    )

    # Load email repository database
    email_repository_db = None
    try:
        # Check if email_repository table exists
        cursor = connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='email_repository';"
        )
        if cursor.fetchone():
            email_repository_db = SQLiteVec(
                table="email_repository",
                connection=connection,
                db_file=db_path,
                embedding=embeddings,
            )
            print("Email repository loaded successfully.")
        else:
            print(
                "Email repository table not found. Email search tool will run in dev mode."
            )
    except Exception as e:
        print(f"Warning: Could not load email repository: {e}")

    return knowledge_db, email_repository_db


def validate_database_health(db_path: str) -> bool:
    """
    Validate that the database is accessible and not corrupted.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        True if database is healthy, False otherwise
    """
    if not os.path.exists(db_path):
        return False

    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        connection.close()
        return len(tables) > 0
    except Exception:
        return False
