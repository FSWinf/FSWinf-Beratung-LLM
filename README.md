# FSWinf FreeScout LLM Integration

A modern, modular Python package for processing FreeScout conversations and generating AI-powered email suggestions using Retrieval-Augmented Generation (RAG).

## 🚀 Features

- **Modular Architecture**: Clean separation of concerns with focused modules
- **Modern Python Tooling**: Built with `uv`, `pyproject.toml`, and development best practices
- **Type Safety**: Full type hints and mypy support
- **Code Quality**: Automated formatting with Black, import sorting with isort, and linting with pylint
- **Testing**: Comprehensive test suite with pytest and coverage reporting
- **Multiple Interfaces**: CLI, Python package, and console scripts

## 📦 Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone <repository-url>
cd freescout-llm

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
uv pip install -e ".[dev]"
```

### Using pip

```bash
pip install -e ".[dev]"
```

## 🏗️ Project Structure

```
freescout-llm/
├── freescout_llm/              # Main package directory
│   ├── __init__.py             # Package initialization and exports
│   ├── __main__.py             # Module entry point (python -m freescout_llm)
│   ├── main.py                 # CLI interface
│   ├── config.py               # Configuration and environment variables
│   ├── freescout_api.py        # FreeScout API client
│   ├── rag_pipeline.py         # RAG pipeline for AI responses
│   ├── text_processing.py     # Text processing utilities
│   ├── conversation_processor.py # Main conversation processing logic
│   ├── server.py               # Web server interface
│   ├── vector_db.py            # Vector database management
│   ├── scrape/                 # Web scraping package
│   │   ├── __init__.py         # Scraper exports
│   │   ├── base.py            # Base scraper classes
│   │   ├── freescout.py       # FreeScout conversation scraper
│   │   ├── tiss.py            # TISS system scraper
│   │   ├── scrapy_scrapers.py # Scrapy-based website scrapers
│   │   ├── cli.py             # Scraper CLI interface
│   │   └── README.md          # Scraper documentation
│   ├── database/               # Database management package
│   │   ├── __init__.py
│   │   ├── document_loaders.py
│   │   ├── document_processors.py
│   │   └── vector_db_manager.py
│   └── tools/                  # LangChain tools package
│       ├── __init__.py
│       ├── knowledge_search.py
│       ├── email_search.py
│       └── url_summarization.py
├── tests/                      # Test suite
│   ├── __init__.py
│   └── test_text_processing.py
├── knowledge_base/             # Knowledge base storage
├── email_chains/               # Email conversation storage
├── pyproject.toml              # Project configuration and dependencies
├── Makefile                    # Development commands
├── .pre-commit-config.yaml     # Pre-commit hooks configuration
├── README.md                   # This file
└── main.py                     # Legacy wrapper
```

## 🔧 Usage

### Command Line Interface

```bash
# Using the installed console script
freescout-llm 12345

# Using the module
python -m freescout_llm 12345

# Legacy wrapper
python main.py 12345

# Available options
freescout-llm --force 12345        # Force processing (bypass checks)
freescout-llm --stream-only 12345  # Stream output only (don't create note)
```

### Python Package

```python
from freescout_llm import ConversationProcessor

# Initialize processor
processor = ConversationProcessor()

if processor.is_ready():
    # Process a conversation
    success = processor.process_conversation(
        conversation_id=12345,
        force=False,
        stream_only=True
    )
    print(f"Processing successful: {success}")
```

### Individual Components

```python
from freescout_llm import FreeScoutAPI, RAGPipeline, markdown_to_html
from freescout_llm.scrape import FreescoutScraper, TISSScraper

# Use FreeScout API
api = FreeScoutAPI()
conversation = api.get_conversation(12345)

# Use RAG pipeline
rag = RAGPipeline()
if rag.is_ready():
    suggestion = rag.generate_suggestion("Question text", "Subject")

# Use text processing
html = markdown_to_html("**Bold text**")

# Use scrapers for knowledge base generation
scraper = FreescoutScraper()
scraper.run()

tiss_scraper = TISSScraper()
tiss_scraper.run()
```

### Web Scraping

The package includes a comprehensive scraping system for building knowledge bases:

```bash
# Scrape all sources
python -m freescout_llm.scrape.cli all

# Scrape specific sources
python -m freescout_llm.scrape.cli freescout
python -m freescout_llm.scrape.cli tiss
python -m freescout_llm.scrape.cli htu

# Use custom output directory
python -m freescout_llm.scrape.cli tiss --output-dir /custom/path
```

Available scrapers:
- **freescout**: FreeScout email conversations
- **tiss**: TU Wien TISS system
- **htu**: HTU Vienna student union
- **informatics**: TU Wien Informatics faculty
- **tuwien**: TU Wien main website
- **vowi**: VoWi student course database
- **winf**: Business Informatics program

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
make install-dev
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test

# Run tests with coverage
make test-cov
```

### Available Make Commands

```bash
make help              # Show available commands
make install           # Install package in development mode
make install-dev       # Install with development dependencies
make format            # Format code with black and isort
make lint              # Run pylint and mypy
make test              # Run tests
make test-cov          # Run tests with coverage
make clean             # Clean build artifacts
make build             # Build the package
```

## 📋 Requirements

- Python 3.9+
- All dependencies are managed in `pyproject.toml`

### Core Dependencies

- `python-dotenv`: Environment variable management
- `requests`: HTTP client for FreeScout API
- `beautifulsoup4`: HTML parsing
- `langchain`: LLM framework
- `ollama`: Local LLM integration
- `sqlite-vec`: Vector database

### Development Dependencies

- `black`: Code formatting
- `isort`: Import sorting
- `pylint`: Code linting
- `mypy`: Type checking
- `pytest`: Testing framework

## ⚙️ Configuration

Required environment variables (managed in `.env` file):

```bash
FREESCOUT_BASE_URL=https://your-freescout-instance.com
FREESCOUT_API_KEY=your_api_key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_EMBEDDING_MODEL=llama2  # Optional, defaults to OLLAMA_MODEL
LLM_USER_ID=123
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=freescout_llm

# Run specific test file
pytest tests/test_text_processing.py -v
```

## 📝 Code Quality Standards

This project follows modern Python development practices:

- **PEP 8** compliance via Black formatting
- **Type hints** throughout the codebase
- **Docstrings** for all public functions and classes
- **Import sorting** with isort
- **Linting** with pylint

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `make install-dev`
4. Make your changes
5. Run tests: `make test`
6. Run linting: `make lint`
7. Submit a pull request
