"""
LLM provider utilities for the RAG pipeline.
Handles initialization of different LLM and embedding providers.
"""

from typing import Any, Tuple


def initialize_embeddings(provider: str, **kwargs) -> Any:
    """
    Initialize embeddings based on the provider.

    Args:
        provider: The embeddings provider ("openai" or "ollama")
        **kwargs: Provider-specific configuration

    Returns:
        Initialized embeddings instance
    """
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=kwargs.get("model"),
            openai_api_base=kwargs.get("base_url"),
            openai_api_key=kwargs.get("api_key"),
        )
    else:  # ollama
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=kwargs.get("model"), base_url=kwargs.get("base_url")
        )


def initialize_chat_llm(provider: str, **kwargs) -> Any:
    """
    Initialize chat LLM based on the provider.

    Args:
        provider: The chat provider ("openai" or "ollama")
        **kwargs: Provider-specific configuration

    Returns:
        Initialized chat LLM instance
    """
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=kwargs.get("model"),
            openai_api_base=kwargs.get("base_url"),
            openai_api_key=kwargs.get("api_key"),
        )
    else:  # ollama
        from langchain_ollama import ChatOllama

        return ChatOllama(model=kwargs.get("model"), base_url=kwargs.get("base_url"))


def initialize_llm_providers(
    embeddings_provider: str,
    chat_provider: str,
    embeddings_config: dict,
    chat_config: dict,
) -> Tuple[Any, Any]:
    """
    Initialize both embeddings and chat LLM providers.

    Args:
        embeddings_provider: The embeddings provider name
        chat_provider: The chat provider name
        embeddings_config: Configuration for embeddings
        chat_config: Configuration for chat LLM

    Returns:
        Tuple of (embeddings, chat_llm) instances
    """
    embeddings = initialize_embeddings(embeddings_provider, **embeddings_config)
    chat_llm = initialize_chat_llm(chat_provider, **chat_config)

    return embeddings, chat_llm
