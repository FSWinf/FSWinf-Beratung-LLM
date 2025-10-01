.PHONY: help install install-dev format lint test clean build
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	uv pip install -e .

install-dev: ## Install development dependencies
	uv pip install -e ".[dev]"

format: ## Format code with black and isort
	black freescout_llm/ tests/ *.py
	isort freescout_llm/ tests/ *.py

lint: ## Run linting tools
	pylint freescout_llm/
	mypy freescout_llm/

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=freescout_llm --cov-report=html --cov-report=term

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	uv build