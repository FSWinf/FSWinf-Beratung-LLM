#!/usr/bin/env python3
"""
Example script demonstrating how to use the modular FreeScout LLM system.

This shows how individual components can be used independently or together.
"""

from freescout_llm.config import validate_config
from freescout_llm.conversation_processor import ConversationProcessor
from freescout_llm.freescout_api import FreeScoutAPI
from freescout_llm.rag_pipeline import RAGPipeline
from freescout_llm.text_processing import html_to_markdown, markdown_to_html


def example_api_usage():
    """Example of using the FreeScout API module independently."""
    print("=== FreeScout API Example ===")

    # Validate configuration first
    validate_config()

    # Create API client
    api = FreeScoutAPI()

    # Example: Fetch a conversation (replace with actual ID)
    # conversation = api.get_conversation(12345)
    # if conversation:
    #     print(f"Conversation subject: {conversation.get('subject', 'No subject')}")

    print("FreeScout API client initialized successfully!")


def example_rag_usage():
    """Example of using the RAG pipeline independently."""
    print("\n=== RAG Pipeline Example ===")

    # Create RAG pipeline
    rag = RAGPipeline()

    if rag.is_ready():
        print("RAG pipeline is ready!")

        # Example: Generate suggestion (uncomment to test with real data)
        # suggestion = rag.generate_suggestion(
        #     "Ich brauche Hilfe mit meiner Bachelorarbeit...",
        #     "Frage zur Bachelorarbeit"
        # )
        # print(f"Generated suggestion: {suggestion[:100]}...")

        # Example: Test individual tools from the modular architecture
        print("\nTesting modular tools...")

        # Import individual tool creators
        from freescout_llm.tools import (
            create_email_search_tool,
            create_knowledge_search_tool,
            create_url_summarization_tool,
        )

        # Test knowledge search tool
        knowledge_tool = create_knowledge_search_tool(rag.vector_db)
        print("Knowledge search tool created successfully!")

        # Test email search tool
        email_tool = create_email_search_tool(rag.email_repository_db)
        print("Email search tool created successfully!")

        # Test URL summarization tool
        url_tool = create_url_summarization_tool(rag.llm)
        print("URL summarization tool created successfully!")

        # Example with a university URL (uncomment to test)
        # result = url_tool.invoke({
        #     "url": "https://www.tuwien.at/studium/studieninteresse/bachelor",
        #     "reason": "Information about bachelor programs at TU Wien"
        # })
        # print(f"URL summary: {result[:200]}...")

        # Example with PDF (uncomment to test)
        # result = url_tool.invoke({
        #     "url": "https://tiss.tuwien.ac.at/some-document.pdf",
        #     "reason": "Course syllabus information"
        # })
        # print(f"PDF summary: {result[:200]}...")

        print("All modular tools initialized successfully!")
        print(
            "Supported domains: tuwien.at, winf.at, htu.at, fsinf.at, vowi.fsinf.at, informatics.tuwien.ac.at"
        )
        print("Supported formats: HTML (converted to Markdown), PDF")
        print("Architecture: Modular design with separate tool modules")
    else:
        print("RAG pipeline is not ready. Check vector database.")


def example_text_processing():
    """Example of using text processing utilities."""
    print("\n=== Text Processing Example ===")

    # Example markdown
    markdown_text = """
    # Hallo!
    
    Das ist eine **wichtige** Nachricht mit:
    - Punkt 1
    - Punkt 2
    
    Mehr Infos auf [unserer Website](https://example.com).
    """

    # Convert to HTML
    html_text = markdown_to_html(markdown_text)
    print("Markdown converted to HTML:")
    print(html_text[:200] + "...")

    # Convert back to markdown
    back_to_markdown = html_to_markdown(html_text)
    print("\nHTML converted back to markdown:")
    print(back_to_markdown[:200] + "...")


def example_full_processor():
    """Example of using the full conversation processor."""
    print("\n=== Full Processor Example ===")

    # Create processor
    processor = ConversationProcessor()

    if processor.is_ready():
        print("Conversation processor is ready!")

        # Example: Process a conversation (replace with actual ID)
        # success = processor.process_conversation(12345, stream_only=True)
        # print(f"Processing successful: {success}")
    else:
        print(
            "Conversation processor is not ready. Check configuration and vector database."
        )


def example_vector_db():
    """Example of using the vector database generator."""
    print("\n=== Vector Database Example ===")

    # Create vector database generator
    from freescout_llm import VectorDatabaseGenerator

    generator = VectorDatabaseGenerator()
    print("Vector database generator initialized!")

    # Example: Generate database (uncomment to test with real data)
    # success = generator.generate(force=False)
    # print(f"Database generation successful: {success}")


def example_server():
    """Example of using the webhook server."""
    print("\n=== Webhook Server Example ===")

    from freescout_llm import FreeScoutWebhookServer

    # Create server (don't start it in example)
    server = FreeScoutWebhookServer(host="127.0.0.1", port=5001, debug=True)
    print("Webhook server initialized!")

    # Example: Start server (uncomment to test)
    # server.run()


def example_cli_usage():
    """Example of CLI usage."""
    print("\n=== CLI Usage Examples ===")

    print("Available CLI commands:")
    print("  freescout-llm process 12345")
    print("  freescout-llm process 12345 --force --stream-only")
    print("  freescout-llm generate-db")
    print("  freescout-llm generate-db --force")
    print("  freescout-llm server")
    print("  freescout-llm server --host 127.0.0.1 --port 5002 --debug")
    print("")
    print("Legacy compatibility:")
    print("  python main.py 12345  # Automatically converts to 'process' subcommand")
    print("  python -m freescout_llm process 12345")


if __name__ == "__main__":
    print("FreeScout LLM Integration - Module Examples")
    print("=" * 50)

    try:
        example_api_usage()
        example_rag_usage()
        example_text_processing()
        example_full_processor()
        example_vector_db()
        example_server()
        example_cli_usage()

        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nTo process a real conversation, use:")
        print("freescout-llm process <conversation_id>")
        print("\nTo generate the vector database, use:")
        print("freescout-llm generate-db")
        print("\nTo start the webhook server, use:")
        print("freescout-llm server")

    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure your .env file is configured correctly.")
