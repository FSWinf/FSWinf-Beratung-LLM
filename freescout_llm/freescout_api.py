"""
FreeScout API client module.
Handles all interactions with the FreeScout API.
"""

from typing import Dict, Optional

import requests

from .config import FREESCOUT_API_KEY, FREESCOUT_BASE_URL, LLM_USER_ID


class FreeScoutAPI:
    """Client for interacting with the FreeScout API."""

    def __init__(self):
        self.base_url = FREESCOUT_BASE_URL
        self.headers = {"X-FreeScout-API-Key": FREESCOUT_API_KEY}

    def get_conversation(self, conversation_id: int) -> Optional[Dict]:
        """
        Fetches a conversation from FreeScout.

        Args:
            conversation_id: The ID of the conversation to fetch

        Returns:
            Dictionary containing conversation data, or None if error
        """
        url = f"{self.base_url}/api/conversations/{conversation_id}"
        print(f"Fetching conversation {conversation_id}...")

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            print("Successfully fetched conversation.")
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching conversation from FreeScout: {e}")
            return None

    def create_note(self, conversation_id: int, text: str) -> bool:
        """
        Creates a note in a FreeScout conversation.

        Args:
            conversation_id: The ID of the conversation
            text: The note content (HTML)

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/conversations/{conversation_id}/threads"
        payload = {"type": "note", "text": text, "user": LLM_USER_ID, "imported": True}

        print("Creating note in FreeScout...")
        try:
            response = requests.post(
                url, headers=self.headers, json=payload, timeout=30
            )
            response.raise_for_status()
            print("Successfully created note.")
            return True
        except requests.RequestException as e:
            print(f"Error creating note in FreeScout: {e}")
            print(f"Response body: {e.response.text if e.response else 'No response'}")
            return False
