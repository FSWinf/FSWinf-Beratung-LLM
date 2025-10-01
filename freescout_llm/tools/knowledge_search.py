"""
Knowledge base search tool for the RAG pipeline.
Provides semantic search capabilities over the vector database.
"""

from langchain.tools import tool


def create_knowledge_search_tool(vector_db):
    """
    Creates a tool that allows the LLM to search the vector database.

    Args:
        vector_db: The vector database instance (SQLiteVec)

    Returns:
        The knowledge search tool function
    """

    @tool
    def search_knowledge_base(query: str, k: int = 5) -> str:
        """
        Search the knowledge base for relevant information using semantic search.

        Args:
            query: The search query to find relevant documents
            k: Number of documents to retrieve (default: 5, max: 10)

        Returns:
            String containing the most relevant documents found
        """
        if not vector_db:
            return f"[DEV MODE] Vector database not available. Would search for: '{query}' (k={k})"

        # Limit k to prevent excessive results
        k = min(max(1, k), 10)

        try:
            print(f"\n[Tool] Searching knowledge base for: '{query}' (k={k})")

            # Perform similarity search
            docs = vector_db.similarity_search(query, k=k)

            if not docs:
                return f"No relevant documents found for query: '{query}'"

            # Format the results
            results = []
            for i, doc in enumerate(docs, 1):
                source_url = doc.metadata.get("source_url", "")
                content = doc.page_content.strip()

                result = f"Document {i}:\n{content}"
                if source_url:
                    result += f"\nURL: {source_url}"
                results.append(result)

            formatted_results = "\n\n---\n\n".join(results)
            print(f"[Tool] Found {len(docs)} relevant documents")

            return formatted_results

        except Exception as e:
            error_msg = f"Error searching knowledge base: {str(e)}"
            print(f"[Tool Error] {error_msg}")
            return error_msg

    return search_knowledge_base
