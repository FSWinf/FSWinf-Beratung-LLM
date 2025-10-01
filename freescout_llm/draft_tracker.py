"""
Draft tracking module for the FreeScout LLM integration.
Handles tracking of when LLM drafts were created for each conversation.
"""

import sqlite3
from datetime import datetime
from typing import Optional

from .config import DRAFT_TRACKER_DB_PATH


class DraftTracker:
    """Tracks when LLM drafts were created for conversations."""

    def __init__(self, db_path: str = None):
        """
        Initialize the draft tracker.

        Args:
            db_path: Path to the SQLite database file for tracking drafts.
                    If None, uses the configured DRAFT_TRACKER_DB_PATH.
        """
        self.db_path = db_path or DRAFT_TRACKER_DB_PATH
        self._init_database()

    def _init_database(self):
        """Initialize the database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_drafts (
                    conversation_id INTEGER PRIMARY KEY,
                    last_draft_created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            conn.commit()

    def record_draft_created(self, conversation_id: int, created_at: str):
        """
        Record that a draft was created for a conversation.

        Args:
            conversation_id: The ID of the conversation
            created_at: ISO format timestamp when the draft was created
        """
        current_time = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO conversation_drafts 
                (conversation_id, last_draft_created_at, updated_at)
                VALUES (?, ?, ?)
            """,
                (conversation_id, created_at, current_time),
            )
            conn.commit()

    def get_last_draft_time(self, conversation_id: int) -> Optional[str]:
        """
        Get the timestamp of the last draft created for a conversation.

        Args:
            conversation_id: The ID of the conversation

        Returns:
            ISO format timestamp of last draft, or None if no draft recorded
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT last_draft_created_at 
                FROM conversation_drafts 
                WHERE conversation_id = ?
            """,
                (conversation_id,),
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def should_create_draft(self, conversation_id: int, threads: list) -> bool:
        """
        Determine if a new draft should be created based on thread timestamps.

        Args:
            conversation_id: The ID of the conversation
            threads: List of conversation threads (newest first from API)

        Returns:
            True if a new draft should be created, False otherwise
        """
        last_draft_time = self.get_last_draft_time(conversation_id)

        # If no draft was ever created, we should create one
        if not last_draft_time:
            return True

        # Find the newest non-LLM thread
        from .config import LLM_USER_ID

        for thread in threads:
            # Skip LLM-created threads (notes and drafts)
            if (
                thread["type"] == "note"
                and thread.get("createdBy", {}).get("id") == LLM_USER_ID
            ):
                continue

            # Check if this thread is newer than our last draft
            thread_created_at = thread.get("createdAt")
            if thread_created_at and thread_created_at > last_draft_time:
                return True

        return False
