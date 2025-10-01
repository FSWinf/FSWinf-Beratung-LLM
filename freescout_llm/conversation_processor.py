"""
Conversation processing module for the FreeScout LLM integration.
Handles conversation analysis and response generation workflow.
"""

from datetime import datetime

from .draft_tracker import DraftTracker
from .freescout_api import FreeScoutAPI
from .rag_pipeline import RAGPipeline
from .text_processing import html_to_markdown, markdown_to_html, sanitize_html


class ConversationProcessor:
    """Processes FreeScout conversations and generates AI suggestions."""

    def __init__(self):
        self.api = FreeScoutAPI()
        self.rag = RAGPipeline()
        self.draft_tracker = DraftTracker()  # Uses configured path by default

    def is_ready(self) -> bool:
        """
        Checks if the processor is ready to handle conversations.

        Returns:
            True if RAG pipeline is ready, False otherwise
        """
        return self.rag.is_ready()

    def process_conversation(
        self, conversation_id: int, force: bool = False, stream_only: bool = False
    ) -> bool:
        """
        Processes a conversation and generates an AI suggestion.

        Args:
            conversation_id: The ID of the conversation to process
            force: Skip certain checks and force processing
            stream_only: Only stream output without creating a note

        Returns:
            True if processing was successful, False otherwise
        """
        # Fetch conversation data
        conversation = self.api.get_conversation(conversation_id)
        if not conversation:
            return False

        # Extract and filter threads
        threads = self._extract_threads(conversation)
        if not threads:
            print("Conversation has no threads. Exiting.")
            return False

        # Check if processing should be skipped
        if not force and self._should_skip_processing(threads, conversation_id):
            return True

        # Remove last user reply if forcing and it exists
        if force and threads[-1]["type"] == "message":
            threads = threads[:-1]

        # Extract conversation text
        conversation_text = self._extract_conversation_text(threads)
        if not conversation_text.strip():
            print("No customer messages found to process. Exiting.")
            return False

        # Generate suggestion
        subject = conversation.get("subject", "No Subject")
        suggestion = self.rag.generate_suggestion(conversation_text, subject)

        if not suggestion:
            print(f"Failed to generate suggestion for conversation {conversation_id}.")
            return False

        # Handle output
        if stream_only:
            print(
                f"\n[Stream Only Mode] Generated suggestion for conversation {conversation_id}."
            )
            print("Draft creation skipped due to --stream-only flag.")
            return True
        else:
            return self._create_suggestion_draft(conversation_id, suggestion)

    def _extract_threads(self, conversation: dict) -> list:
        """
        Extracts and filters threads from conversation data.

        Args:
            conversation: Raw conversation data from API

        Returns:
            List of filtered threads, oldest first
        """
        threads = conversation.get("_embedded", {}).get("threads", [])
        # Filter out lineitem threads and reverse to have oldest first
        filtered_threads = [
            thread
            for thread in threads
            if thread["type"] in ["customer", "message", "note"]
        ]
        return filtered_threads[::-1]

    def _should_skip_processing(self, threads: list, conversation_id: int) -> bool:
        """
        Determines if conversation processing should be skipped.

        Args:
            threads: List of conversation threads
            conversation_id: The ID of the conversation

        Returns:
            True if processing should be skipped, False otherwise
        """
        if not threads:
            return True

        last_thread = threads[-1]

        # Skip if last thread is a user reply
        if last_thread["type"] == "message":
            print("The last message is a user reply. Skipping.")
            return True

        # Use draft tracker to determine if we should create a new draft
        if not self.draft_tracker.should_create_draft(conversation_id, threads):
            print("No new activity since last LLM draft. Skipping.")
            return True

        return False

    def _extract_conversation_text(self, threads: list) -> str:
        """
        Extracts text content from conversation threads.

        Args:
            threads: List of conversation threads

        Returns:
            Combined conversation text in markdown format
        """
        conversation_text = ""
        for thread in threads:
            if thread["type"] in ["customer", "message"]:
                body_html = thread["body"]
                body_text = html_to_markdown(body_html)
                conversation_text += f"{body_text}\n\n"
        return conversation_text

    def _create_suggestion_draft(self, conversation_id: int, suggestion: str) -> bool:
        """
        Creates a draft message with the AI suggestion in the conversation.

        Args:
            conversation_id: The ID of the conversation
            suggestion: The generated suggestion in markdown format

        Returns:
            True if draft was created successfully, False otherwise
        """
        suggestion_html = markdown_to_html(suggestion)
        suggestion_html = sanitize_html(suggestion_html)
        draft_text = f"<div>{suggestion_html}</div>"

        if self.api.create_draft(conversation_id, draft_text):
            # Record the draft creation with current timestamp
            current_time = datetime.now().isoformat()
            self.draft_tracker.record_draft_created(conversation_id, current_time)
            print(f"Process for conversation {conversation_id} completed successfully.")
            return True
        else:
            print(f"Failed to create draft for conversation {conversation_id}.")
            return False
