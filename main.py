#!/usr/bin/env python3
"""
Legacy wrapper for the FreeScout LLM Integration CLI.

This wrapper provides backward compatibility for the old CLI interface.
For new usage, use 'freescout-llm' command or 'python -m freescout_llm' instead.

Usage:
    python main.py <conversation_id> [--force] [--stream-only]  # Legacy format
    python main.py process <conversation_id> [--force] [--stream-only]  # New format
"""

import sys

from freescout_llm.main import main

if __name__ == "__main__":
    # Check if the first argument looks like a conversation ID (legacy usage)
    if len(sys.argv) >= 2 and sys.argv[1].isdigit():
        # Legacy usage: python main.py 12345 [--force] [--stream-only]
        # Transform to new format: process 12345 [--force] [--stream-only]
        sys.argv.insert(1, "process")

    main()
