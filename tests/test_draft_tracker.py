"""
Tests for draft tracking functionality.
"""

import os
import tempfile

from freescout_llm.draft_tracker import DraftTracker


class TestDraftTracker:
    """Test cases for draft tracking functionality."""

    def test_draft_tracker_initialization(self):
        """Test that draft tracker initializes correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_draft_tracker.sqlite")
            DraftTracker(db_path)

            # Check that database file was created
            assert os.path.exists(db_path)

    def test_record_and_retrieve_draft(self):
        """Test recording and retrieving draft timestamps."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_draft_tracker.sqlite")
            tracker = DraftTracker(db_path)

            conversation_id = 123
            created_at = "2024-01-15T10:30:00Z"

            # Record a draft
            tracker.record_draft_created(conversation_id, created_at)

            # Retrieve the timestamp
            result = tracker.get_last_draft_time(conversation_id)
            assert result == created_at

    def test_get_nonexistent_draft_time(self):
        """Test retrieving timestamp for a conversation with no drafts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_draft_tracker.sqlite")
            tracker = DraftTracker(db_path)

            # Try to get timestamp for nonexistent conversation
            result = tracker.get_last_draft_time(999)
            assert result is None

    def test_should_create_draft_no_previous_draft(self):
        """Test that we should create a draft when none exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_draft_tracker.sqlite")
            tracker = DraftTracker(db_path)

            conversation_id = 123
            threads = [
                {
                    "type": "customer",
                    "createdAt": "2024-01-15T10:30:00Z",
                    "createdBy": {"id": 456},
                }
            ]

            # Should create draft when none exists
            assert tracker.should_create_draft(conversation_id, threads)

    def test_should_create_draft_new_activity(self):
        """Test that we should create a draft when there's new activity."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_draft_tracker.sqlite")
            tracker = DraftTracker(db_path)

            conversation_id = 123

            # Record an old draft
            old_time = "2024-01-15T10:30:00Z"
            tracker.record_draft_created(conversation_id, old_time)

            # New thread after the draft
            threads = [
                {
                    "type": "customer",
                    "createdAt": "2024-01-15T11:00:00Z",  # Newer than draft
                    "createdBy": {"id": 456},
                }
            ]

            # Should create draft when there's new activity
            assert tracker.should_create_draft(conversation_id, threads)

    def test_should_not_create_draft_no_new_activity(self):
        """Test that we should not create a draft when there's no new activity."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_draft_tracker.sqlite")
            tracker = DraftTracker(db_path)

            conversation_id = 123

            # Record a recent draft
            recent_time = "2024-01-15T11:00:00Z"
            tracker.record_draft_created(conversation_id, recent_time)

            # Old thread before the draft
            threads = [
                {
                    "type": "customer",
                    "createdAt": "2024-01-15T10:30:00Z",  # Older than draft
                    "createdBy": {"id": 456},
                }
            ]

            # Should not create draft when there's no new activity
            assert not tracker.should_create_draft(conversation_id, threads)

    def test_update_existing_draft_record(self):
        """Test updating an existing draft record."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_draft_tracker.sqlite")
            tracker = DraftTracker(db_path)

            conversation_id = 123

            # Record first draft
            first_time = "2024-01-15T10:30:00Z"
            tracker.record_draft_created(conversation_id, first_time)

            # Record second draft (should update)
            second_time = "2024-01-15T11:00:00Z"
            tracker.record_draft_created(conversation_id, second_time)

            # Should return the most recent time
            result = tracker.get_last_draft_time(conversation_id)
            assert result == second_time
