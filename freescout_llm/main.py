#!/usr/bin/env python3
"""
FreeScout LLM Integration - Main CLI Interface

This script provides multiple commands for the FreeScout LLM integration:
- process: Process a specific conversation
- generate-db: Generate/update both email repository and knowledge base vector databases
- server: Start the webhook server

Usage:
    freescout-llm process [--force] [--stream-only] <conversation_id>
    freescout-llm generate-db [--force]
    freescout-llm server [--host HOST] [--port PORT] [--debug]
"""

import argparse
import sys

from .config import validate_config
from .conversation_processor import ConversationProcessor
from .server import start_server_command
from .vector_db import generate_all_databases


def process_command(args) -> None:
    """Handle the process subcommand."""
    # Validate configuration
    validate_config()

    # Initialize processor
    processor = ConversationProcessor()
    if not processor.is_ready():
        print("Exiting due to RAG pipeline setup failure.")
        sys.exit(1)

    # Process conversation
    try:
        success = processor.process_conversation(
            args.conversation_id, args.force, args.stream_only
        )

        if not success:
            print(f"Failed to process conversation {args.conversation_id}.")
            sys.exit(1)

    except ValueError:
        print("Error: The conversation_id must be an integer.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def generate_db_command(args) -> None:
    """Handle the generate-db subcommand."""
    # Validate configuration
    validate_config()

    try:
        print("Generating both email repository and knowledge base databases...")
        success = generate_all_databases(force=args.force)
        if not success:
            print("Database generation failed.")
            sys.exit(1)
        print("Database generation completed successfully!")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def server_command(args) -> None:
    """Handle the server subcommand."""
    # Validate configuration
    validate_config()

    try:
        start_server_command(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the FreeScout LLM integration."""
    parser = argparse.ArgumentParser(
        description="FreeScout LLM Integration - AI-powered email suggestions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Process command
    process_parser = subparsers.add_parser(
        "process", help="Process a FreeScout conversation and generate AI suggestions"
    )
    process_parser.add_argument(
        "--force",
        action="store_true",
        help="Force processing by bypassing certain checks",
    )
    process_parser.add_argument(
        "--stream-only",
        action="store_true",
        help="Only stream the output without creating a note in the conversation",
    )
    process_parser.add_argument(
        "conversation_id", type=int, help="The ID of the conversation to process"
    )
    process_parser.set_defaults(func=process_command)

    # Generate database command
    generate_parser = subparsers.add_parser(
        "generate-db",
        help="Generate or update both email repository and knowledge base vector databases",
    )
    generate_parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if databases are up to date",
    )
    generate_parser.set_defaults(func=generate_db_command)

    # Server command
    server_parser = subparsers.add_parser(
        "server", help="Start the webhook server for automatic processing"
    )
    server_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="Port to bind the server to (default: 5001)",
    )
    server_parser.add_argument(
        "--debug", action="store_true", help="Run server in debug mode"
    )
    server_parser.set_defaults(func=server_command)

    # Parse arguments
    args = parser.parse_args()

    # If no command is provided, show help
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute the appropriate command
    args.func(args)


if __name__ == "__main__":
    main()
