#!/usr/bin/env python3
"""
Flask Server Module

Provides a webhook server for processing FreeScout conversations automatically.
"""

import threading
from queue import Queue
from typing import Tuple

from flask import Flask, jsonify, request

from .conversation_processor import ConversationProcessor


class FreeScoutWebhookServer:
    """Flask server for handling FreeScout webhooks."""

    def __init__(self, host: str = "0.0.0.0", port: int = 5001, debug: bool = False):
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.debug = debug
        self.conversation_queue = Queue()
        self.processor = ConversationProcessor()

        # Setup routes
        self._setup_routes()

        # Start worker thread
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def _setup_routes(self) -> None:
        """Setup Flask routes."""

        @self.app.route("/webhook", methods=["POST"])
        def webhook():
            """Handle incoming POST requests from the webhook."""
            return self._handle_webhook()

        @self.app.route("/health", methods=["GET"])
        def health():
            """Health check endpoint."""
            return jsonify(
                {"status": "healthy", "queue_size": self.conversation_queue.qsize()}
            )

    def _process_queue(self) -> None:
        """Continuously process items from the queue."""
        while True:
            conversation_id = self.conversation_queue.get()
            try:
                print(f"Processing conversation {conversation_id} from queue...")
                success = self.processor.process_conversation(conversation_id)
                if success:
                    print(f"Successfully processed conversation {conversation_id}")
                else:
                    print(f"Failed to process conversation {conversation_id}")
            except Exception as e:
                print(f"Error processing conversation {conversation_id}: {e}")
            finally:
                self.conversation_queue.task_done()

    def _handle_webhook(self) -> Tuple[dict, int]:
        """Handle webhook requests."""
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        conversation_id = data.get("id")

        if not conversation_id:
            return jsonify({"error": "Missing 'id' in request payload"}), 400

        # Add the task to the queue
        self.conversation_queue.put(conversation_id)
        print(f"Added conversation {conversation_id} to processing queue")

        return (
            jsonify(
                {
                    "message": "Successfully added to the processing queue.",
                    "conversation_id": conversation_id,
                }
            ),
            200,
        )

    def run(self) -> None:
        """Start the Flask server."""
        if not self.processor.is_ready():
            print(
                "Warning: RAG pipeline is not ready. Server will start but processing may fail."
            )

        print(f"Starting FreeScout webhook server on {self.host}:{self.port}")
        self.app.run(debug=self.debug, host=self.host, port=self.port)


def start_server_command(
    host: str = "0.0.0.0", port: int = 5001, debug: bool = False
) -> None:
    """Command line interface for starting the webhook server."""
    server = FreeScoutWebhookServer(host=host, port=port, debug=debug)
    server.run()
