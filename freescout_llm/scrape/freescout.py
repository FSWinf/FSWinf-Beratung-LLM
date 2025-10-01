"""
FreeScout conversation scraper.
"""

import os
import urllib.parse
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from .base import BaseScraper

# Load environment variables
load_dotenv()


class FreescoutScraper(BaseScraper):
    """
    Scraper for FreeScout conversations.

    Extracts email conversations from FreeScout and categorizes them
    for use in the knowledge base.
    """

    def __init__(
        self, output_dir: str = "email_chains", mailbox_id: int = 3, page_size: int = 10
    ):
        """
        Initialize the FreeScout scraper.

        Args:
            output_dir: Directory to save email chains
            mailbox_id: FreeScout mailbox ID to scrape
            page_size: Number of conversations per API request
        """
        super().__init__("", output_dir)  # No base URL for API scraper

        self.freescout_base_url = os.getenv("FREESCOUT_BASE_URL")
        self.api_key = os.getenv("FREESCOUT_API_KEY")

        if not self.freescout_base_url or not self.api_key:
            raise ValueError(
                "FREESCOUT_BASE_URL and FREESCOUT_API_KEY must be set in environment"
            )

        self.mailbox_id = mailbox_id
        self.page_size = page_size

        # Create session with authentication
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-FreeScout-API-Key": self.api_key,
                "Content-Type": "application/json",
            }
        )

        # Create category folders
        self.categories = [
            "course_registration",
            "exam_issues",
            "technical_support",
            "general_inquiries",
        ]

        for category in self.categories:
            (self.output_dir / category).mkdir(parents=True, exist_ok=True)

    def extract_text_from_html(self, html_content: str) -> str:
        """
        Extract plain text from HTML content.

        Args:
            html_content: HTML content to extract text from

        Returns:
            Plain text content
        """
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    def categorize_conversation(self, subject: str, content: str) -> str:
        """
        Categorize conversation based on subject and content.

        Args:
            subject: Email subject line
            content: Email content

        Returns:
            Category name
        """
        subject_lower = subject.lower()
        content_lower = content.lower()

        # Course registration and enrollment
        if any(
            keyword in subject_lower or keyword in content_lower
            for keyword in [
                "anmeldung",
                "registration",
                "einschreibung",
                "enrollment",
                "lva",
                "kurs",
                "course",
                "vorlesung",
                "lecture",
                "tiss",
                "studienplan",
                "curriculum",
            ]
        ):
            return "Course Registration"

        # Exam-related issues
        if any(
            keyword in subject_lower or keyword in content_lower
            for keyword in [
                "prüfung",
                "exam",
                "test",
                "note",
                "grade",
                "bewertung",
                "beurteilung",
                "zeugnis",
                "transcript",
            ]
        ):
            return "Exam Issues"

        # Technical support
        if any(
            keyword in subject_lower or keyword in content_lower
            for keyword in [
                "fehler",
                "error",
                "problem",
                "technisch",
                "technical",
                "support",
            ]
        ):
            return "Technical Support"

        # General inquiries
        return "General Inquiries"

    def extract_tags(self, subject: str, conversation_content: str) -> str:
        """
        Extract relevant tags from the conversation.

        Args:
            subject: Email subject
            conversation_content: Full conversation content

        Returns:
            Comma-separated tags
        """
        tags = []
        subject_lower = subject.lower()
        content_lower = conversation_content.lower()

        # Technology tags
        if "tiss" in subject_lower or "tiss" in content_lower:
            tags.append("TISS")
        if "moodle" in subject_lower or "moodle" in content_lower:
            tags.append("Moodle")

        # Study program tags
        if any(
            keyword in subject_lower or keyword in content_lower
            for keyword in ["bachelor", "wirtschaftsinformatik", "business informatics"]
        ):
            tags.append("Bachelor")
        if any(
            keyword in subject_lower or keyword in content_lower
            for keyword in ["master", "data science"]
        ):
            tags.append("Master")

        # Issue type tags
        if any(
            keyword in subject_lower or keyword in content_lower
            for keyword in ["international", "austausch", "exchange"]
        ):
            tags.append("International Students")
        if any(
            keyword in subject_lower or keyword in content_lower
            for keyword in ["deadline", "frist", "termin"]
        ):
            tags.append("Deadlines")

        return ", ".join(tags) if tags else "General"

    def determine_resolution_status(self, threads: List[Dict]) -> str:
        """
        Determine if the conversation was resolved based on the thread content.

        Args:
            threads: List of conversation threads

        Returns:
            Resolution status description
        """
        if len(threads) < 2:
            return "Single inquiry - no follow-up needed"

        last_thread = threads[-1]
        last_content = last_thread.get("body", "").lower()

        # Look for resolution indicators
        if any(
            phrase in last_content
            for phrase in [
                "danke",
                "thank",
                "gelöst",
                "solved",
                "funktioniert",
                "works",
                "hilft",
            ]
        ):
            return "Issue resolved successfully"

        # Check if last message is from staff (FSWinf response without follow-up)
        if threads[-1].get("type") == "message":
            return "FSWinf response provided - awaiting feedback"

        return "Status unclear - check conversation manually"

    def process_conversation(self, conv: Dict) -> None:
        """
        Process a single conversation and save it to file.

        Args:
            conv: Conversation data from FreeScout API
        """
        threads = conv.get("_embedded", {}).get("threads", [])

        # Filter threads that are not of type "lineitem"
        threads = [
            thread
            for thread in threads
            if thread.get("type") in ["customer", "message"]
        ]

        if not threads:
            print("Conversation has no threads. Skipping.")
            return

        threads = threads[::-1]  # Reverse to have oldest first

        # Extract conversation content for analysis
        conversation_content = ""

        # Separate original inquiry and responses
        original_inquiry = None
        fswinf_responses = []
        follow_ups = []

        for i, thread in enumerate(threads):
            body_text = self.extract_text_from_html(thread["body"])
            created_by = thread.get("createdBy")

            if created_by:
                author_name = f"{created_by.get('firstName', 'Unknown')} {created_by.get('lastName', 'User')}"
            else:
                author_name = "Unknown User"

            conversation_content += f"{body_text} "

            email_part = f"**From: {author_name}**\n\n{body_text.strip()}"

            # Categorize the email part
            if i == 0:  # First message is usually the original inquiry
                original_inquiry = email_part
            elif thread.get("type") == "message":  # FSWinf response (type: "message")
                fswinf_responses.append(email_part)
            else:  # Follow-up from student (type: "customer")
                follow_ups.append(email_part)

        # Determine category and tags
        case_type = self.categorize_conversation(conv["subject"], conversation_content)
        tags = self.extract_tags(conv["subject"], conversation_content)
        resolution = self.determine_resolution_status(threads)

        # Format the email chain document
        email_chain_content = f"""Subject: {conv['subject']}
Date: {conv.get('createdAt', 'Unknown')}
Case Type: {case_type}
Tags: {tags}

---

## Original Inquiry

{original_inquiry or 'No original inquiry found'}

## FSWinf Response

{chr(10).join(fswinf_responses) if fswinf_responses else 'No FSWinf response recorded'}

## Follow-up (if any)

{chr(10).join(follow_ups) if follow_ups else 'No follow-up messages'}

## Resolution

{resolution}

## Notes

Case ID: {conv['id']}
Source URL: {self.freescout_base_url}/conversation/{conv['id']}
Total messages: {len(threads)}
"""

        # Determine subfolder based on category
        category_folder = case_type.lower().replace(" ", "_")
        if category_folder not in self.categories:
            category_folder = "general_inquiries"

        fname = self.output_dir / category_folder / f"case_{conv['id']}.md"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(email_chain_content.strip())
        print(f"Saved conversation {conv['id']} ({case_type}) to {fname}")

    def run(self) -> None:
        """
        Run the FreeScout scraper.
        """
        page = 1

        while True:
            # Build API query parameters
            query_params = {
                "embed": "threads",
                "mailboxId": self.mailbox_id,
                "pageSize": self.page_size,
                "page": page,
            }

            query_string = urllib.parse.urlencode(query_params)
            url = f"{self.freescout_base_url}/api/conversations?{query_string}"

            try:
                response = self.session.get(url)
                response.raise_for_status()

                data = response.json()["_embedded"]["conversations"]
                if not data:
                    break

                for conv in data:
                    self.process_conversation(conv)

                page += 1

            except requests.RequestException as e:
                print(f"Error fetching conversations: {e}")
                break

        print(f"Completed scraping FreeScout conversations to {self.output_dir}")
