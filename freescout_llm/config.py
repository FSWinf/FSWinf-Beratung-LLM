"""
Configuration module for the FreeScout LLM integration.
Handles environment variables and application settings.
"""

import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
FREESCOUT_BASE_URL = os.getenv("FREESCOUT_BASE_URL")
FREESCOUT_API_KEY = os.getenv("FREESCOUT_API_KEY")

# LLM Configuration - supports both Ollama and OpenAI-compatible APIs
# Separate providers for embeddings and chat
EMBEDDINGS_PROVIDER = os.getenv(
    "EMBEDDINGS_PROVIDER", "ollama"
).lower()  # "ollama" or "openai"
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "ollama").lower()  # "ollama" or "openai"

# Legacy provider setting (for backward compatibility)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()  # "ollama" or "openai"

# If the separate providers aren't explicitly set, fall back to the legacy setting
if os.getenv("EMBEDDINGS_PROVIDER") is None:
    EMBEDDINGS_PROVIDER = LLM_PROVIDER
if os.getenv("CHAT_PROVIDER") is None:
    CHAT_PROVIDER = LLM_PROVIDER

# Ollama configuration (legacy)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", OLLAMA_MODEL)

# OpenAI-compatible API configuration (new)
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL", "https://aqueduct.ai.datalab.tuwien.ac.at/v1"
)
OPENAI_API_KEY = os.getenv("AQUEDUCT_API_KEY") or os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "mistral-small-24b")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_MODEL)

# Application settings
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "vector_db.sqlite")

# Validate LLM_USER_ID
try:
    LLM_USER_ID = int(os.getenv("LLM_USER_ID"))
except (ValueError, TypeError):
    print("Error: LLM_USER_ID is not a valid integer in your .env file.")
    sys.exit(1)

# System prompt template
SYSTEM_PROMPT = """Du generierst Email-Antworten für die FSWinf (Fachschaft Wirtschaftsinformatik) an der TU Wien. 
Du hast Zugang zu Tools für die Suche in der Wissensdatenbank und vergangenen Fällen.

ARBEITSWEISE:
Wenn du eine Anfrage erhältst, solltest du zuerst in <think> Tags über die nötigen Schritte nachdenken.
Dann, falls nötig, verwende die verfügbaren Tools.
Abschließend, sobald du alle Informationen hast, liefere eine direkte und saubere Email-Antwort.
**Verwende KEINE <think> Tags in deiner finalen Antwort an den Benutzer.**

EMAIL-FORMAT:
- Beginne mit einer freundlichen Begrüßung
- Schreibe eine vollständige Email-Antwort, die direkt versendet werden kann
- Beende mit einer passenden Verabschiedung und Unterschrift
- Ton: freundlich-professionell, wie von Student zu Student
- **Verwende Markdown-Formatierung** für bessere Lesbarkeit
- Halte dich kurz, und vermeide unnötige Wiederholungen

SPRACHE:
- Antworte IMMER in der gleichen Sprache wie die Anfrage (Englisch → Englisch, Deutsch → Deutsch)
- Verwende "du/Du" (außer bei explizit formellen Anfragen)

INHALTLICHE REGELN:
- Du hast Zugang zu einer Wissensdatenbank und einem Repository vergangener Fälle über die Tools
- Nutze das search_knowledge_base Tool für allgemeine Informationen. Es besteht aus allen relevanten Webseiteinhalten der TU Wien, HTU, und FSWinf
- Nutze das search_past_cases Tool um zu sehen, wie ähnliche Fälle in der Vergangenheit behandelt wurden
- **Zitiere deine Quellen**: Wenn du Informationen aus der Wissensdatenbank oder vergangenen Fällen verwendest, erwähne dies
- **Füge relevante Links hinzu**: Verlinke zu offiziellen TU Wien Seiten, HTU Seiten, oder anderen hilfreichen Ressourcen
- Sei vorsichtig und ehrlich - lieber "weiß ich nicht" als falsche Infos
- Bei Unsicherheit: verweise auf HTU, Studienabteilung oder andere offizielle Stellen

TOOL USAGE:
- Verwende search_knowledge_base für allgemeine Informationen und Dokumentation
- Verwende search_past_cases um ähnliche vergangene Fälle und deren Lösungen zu finden
- Verwende fetch_and_summarize_url um aktuelle Informationen von vertrauenswürdigen Webseiten zu holen
- Du kannst alle Tools verwenden und mehrere Suchanfragen stellen
- Nutze vergangene Fälle als Orientierung, aber aktualisiere Informationen wenn nötig

STRATEGISCHES VORGEHEN:
1. Analysiere die Anfrage und identifiziere das Hauptthema
2. Suche zuerst nach ähnlichen vergangenen Fällen (search_past_cases)
3. Ergänze mit aktuellen Informationen aus der Wissensdatenbank (search_knowledge_base)
4. Falls nötig, hole aktuelle Informationen von offiziellen Webseiten (fetch_and_summarize_url)
5. Kombiniere alle Quellen für eine umfassende und aktuelle Antwort

Du wirst eine Email-Anfrage erhalten. Verwende die verfügbaren Tools bei Bedarf und erstelle dann eine vollständige Email-Antwort.
"""


def validate_config():
    """
    Validates that all required environment variables are set.
    Exits the program if any required variables are missing.
    """
    # Common required variables
    required_vars = [
        FREESCOUT_BASE_URL,
        FREESCOUT_API_KEY,
        LLM_USER_ID,
    ]

    # Provider-specific validation for embeddings
    embeddings_vars = []
    if EMBEDDINGS_PROVIDER == "openai":
        embeddings_vars.extend(
            [
                OPENAI_BASE_URL,
                OPENAI_API_KEY,
                OPENAI_EMBEDDING_MODEL,
            ]
        )
    else:  # ollama
        embeddings_vars.extend(
            [
                OLLAMA_BASE_URL,
                OLLAMA_EMBEDDING_MODEL,
            ]
        )

    # Provider-specific validation for chat
    chat_vars = []
    if CHAT_PROVIDER == "openai":
        chat_vars.extend(
            [
                OPENAI_BASE_URL,
                OPENAI_API_KEY,
                OPENAI_MODEL,
            ]
        )
    else:  # ollama
        chat_vars.extend(
            [
                OLLAMA_BASE_URL,
                OLLAMA_MODEL,
            ]
        )

    # Combine all required variables
    required_vars.extend(embeddings_vars)
    required_vars.extend(chat_vars)

    if not all(required_vars):
        print(
            "Error: One or more environment variables are missing. Please check your .env file."
        )
        print("Required variables: FREESCOUT_BASE_URL, FREESCOUT_API_KEY, LLM_USER_ID")
        print(
            f"Embeddings Provider ({EMBEDDINGS_PROVIDER}): {'OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL' if EMBEDDINGS_PROVIDER == 'openai' else 'OLLAMA_BASE_URL, OLLAMA_EMBEDDING_MODEL'}"
        )
        print(
            f"Chat Provider ({CHAT_PROVIDER}): {'OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL' if CHAT_PROVIDER == 'openai' else 'OLLAMA_BASE_URL, OLLAMA_MODEL'}"
        )
        print(
            "Optional: EMBEDDINGS_PROVIDER (default: ollama), CHAT_PROVIDER (default: ollama)"
        )
        sys.exit(1)

    return True
