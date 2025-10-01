"""
RAG (Retrieval-Augmented Generation) pipeline for the FreeScout LLM integration.
Handles vector database setup, document retrieval, and response generation.
"""

import re
from datetime import datetime
from typing import Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from .config import (
    CHAT_PROVIDER,
    EMBEDDINGS_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_EMBEDDING_MODEL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_MODEL,
    SYSTEM_PROMPT,
    VECTOR_DB_PATH,
)
from .database_utils import setup_vector_database
from .llm_providers import initialize_llm_providers
from .tools import (
    create_email_search_tool,
    create_knowledge_search_tool,
    create_url_summarization_tool,
)


class RAGPipeline:
    """
    Handles the RAG pipeline for generating suggestions.

    This class manages:
    - LLM and embedding model initialization
    - Vector database connections
    - Tool creation and registration
    - Agent setup and execution
    """

    def __init__(self):
        """Initialize the RAG pipeline with all necessary components."""
        self.chain: Optional[AgentExecutor] = None
        self.vector_db = None
        self.email_repository_db = None
        self.embeddings = None
        self.llm = None
        self._setup_pipeline()

    def _setup_pipeline(self) -> None:
        """
        Set up the RAG pipeline by initializing all components.

        This includes:
        1. LLM and embedding provider initialization
        2. Vector database setup
        3. Tool creation
        4. Agent configuration
        """
        try:
            print("Setting up RAG pipeline...")

            # Initialize LLM providers
            embeddings_config = self._get_embeddings_config()
            chat_config = self._get_chat_config()

            self.embeddings, self.llm = initialize_llm_providers(
                EMBEDDINGS_PROVIDER, CHAT_PROVIDER, embeddings_config, chat_config
            )

            # Set up vector databases
            self.vector_db, self.email_repository_db = setup_vector_database(
                VECTOR_DB_PATH, self.embeddings, check_same_thread=False
            )

            # Create and register tools
            tools = self._create_tools()

            # Create agent with dynamic system prompt
            agent_prompt = self._create_agent_prompt()
            agent = create_tool_calling_agent(self.llm, tools, agent_prompt)
            self.chain = AgentExecutor(agent=agent, tools=tools, verbose=True)

            # Print setup summary
            self._print_setup_summary()

        except Exception as e:
            print(f"Error setting up RAG pipeline: {e}")
            print(
                "If the database is corrupted, try regenerating it with 'freescout-llm generate-db --force'"
            )
            self.chain = None

    def _get_embeddings_config(self) -> dict:
        """Get configuration for embeddings provider."""
        if EMBEDDINGS_PROVIDER == "openai":
            return {
                "model": OPENAI_EMBEDDING_MODEL,
                "base_url": OPENAI_BASE_URL,
                "api_key": OPENAI_API_KEY,
            }
        else:  # ollama
            return {
                "model": OLLAMA_EMBEDDING_MODEL,
                "base_url": OLLAMA_BASE_URL,
            }

    def _get_chat_config(self) -> dict:
        """Get configuration for chat LLM provider."""
        if CHAT_PROVIDER == "openai":
            return {
                "model": OPENAI_MODEL,
                "base_url": OPENAI_BASE_URL,
                "api_key": OPENAI_API_KEY,
            }
        else:  # ollama
            return {
                "model": OLLAMA_MODEL,
                "base_url": OLLAMA_BASE_URL,
            }

    def _create_tools(self) -> list:
        """Create and return all available tools for the agent."""
        return [
            create_knowledge_search_tool(self.vector_db),
            create_email_search_tool(self.email_repository_db),
            create_url_summarization_tool(self.llm),
        ]

    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """Create the agent prompt template with current date."""
        current_date = datetime.now().strftime("%d. %B %Y")

        dynamic_system_prompt = f"""Aktuelles Datum: {current_date}

{SYSTEM_PROMPT}

WICHTIG: Berücksichtige das aktuelle Datum bei deinen Antworten. Informationen aus der Wissensdatenbank können älter sein."""

        return ChatPromptTemplate.from_messages(
            [
                ("system", dynamic_system_prompt),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

    def _print_setup_summary(self) -> None:
        """Print a summary of the pipeline setup."""
        print(
            f"RAG pipeline setup complete using {EMBEDDINGS_PROVIDER} embeddings and {CHAT_PROVIDER} chat."
        )

        if self.vector_db:
            print("Knowledge base search tool enabled for enhanced retrieval.")
        else:
            print(
                "Knowledge base search tool enabled in development mode (mock responses)."
            )

        if self.email_repository_db:
            print("Email repository search tool enabled for case history lookup.")
        else:
            print(
                "Email repository search tool enabled in development mode (mock responses)."
            )

        print("URL summarization tool enabled for web content analysis.")

    def is_ready(self) -> bool:
        """
        Check if the RAG pipeline is ready for use.

        Returns:
            True if pipeline is set up correctly, False otherwise
        """
        return self.chain is not None

    def generate_suggestion(self, full_text: str, subject: str) -> str:
        """
        Generate a suggestion using the RAG agent with vector search tools.

        Args:
            full_text: The conversation text
            subject: The email subject

        Returns:
            Complete generated suggestion as string
        """
        if not self.chain:
            return "Error: RAG chain is not available."

        print("\n[RAG Action] Generating suggestion for the following request:")
        question = f"Betreff: {subject}\n\nAnfrage:\n{full_text}"
        print("--------------------------------------------------")
        print(question.strip())
        print("--------------------------------------------------")

        try:
            # Use the agent to process the query
            result = self.chain.invoke({"input": question})

            # Extract the output from the agent result
            if isinstance(result, dict) and "output" in result:
                response = result["output"]
            else:
                response = str(result)

            # Clean up any thinking tags from response
            response = re.sub(
                r"<think>.*?</think>", "", response, flags=re.DOTALL
            ).strip()

            print("\n--- Agent Response ---")
            print(response)
            print("--- End of Response ---\n")

            return response

        except Exception as e:
            error_msg = f"Error generating suggestion: {str(e)}"
            print(f"\n[Error] {error_msg}")
            return error_msg
