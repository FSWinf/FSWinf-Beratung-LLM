"""
Email repository search tool for the RAG pipeline.
Provides search capabilities over past email cases.
"""

from langchain.tools import tool


def create_email_search_tool(email_repository_db):
    """
    Creates a tool that allows the LLM to search past email cases.

    Args:
        email_repository_db: The email repository database instance (SQLiteVec)

    Returns:
        The email search tool function
    """

    @tool
    def search_past_cases(query: str, k: int = 3) -> str:
        """
        Search through past email cases to find similar situations and responses.

        Args:
            query: The search query to find similar past cases
            k: Number of past cases to retrieve (default: 3, max: 8)

        Returns:
            String containing similar past email cases and how they were handled
        """
        if not email_repository_db:
            return f"[DEV MODE] Email repository not available. Would search past cases for: '{query}' (k={k})"

        # Limit k to prevent excessive results
        k = min(max(1, k), 8)

        try:
            print(f"\n[Email Tool] Searching past cases for: '{query}' (k={k})")

            # Perform similarity search on email repository
            docs = email_repository_db.similarity_search(query, k=k)

            if not docs:
                return f"No similar past cases found for query: '{query}'"

            # Format the results
            results = []
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("source", "Unknown")
                email_subject = doc.metadata.get("email_subject", "No subject")
                email_date = doc.metadata.get("email_date", "Unknown date")
                case_type = doc.metadata.get("case_type", "General")
                content = doc.page_content.strip()

                result = f"Past Case {i} - {case_type}\n"
                result += f"Subject: {email_subject}\n"
                result += f"Date: {email_date}\n"
                result += f"Source: {source}\n"
                result += f"Email Exchange:\n{content}"

                results.append(result)

            formatted_results = "\n\n" + "=" * 50 + "\n\n".join(results)
            print(f"[Email Tool] Found {len(docs)} similar past cases")

            return formatted_results

        except Exception as e:
            error_msg = f"Error searching past cases: {str(e)}"
            print(f"[Email Tool Error] {error_msg}")
            return error_msg

    return search_past_cases
