# Makefile for MongoDB GUI project

.PHONY: help install install-dev format lint type-check security test test-cov build clean all

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements.txt -r requirements-dev.txt

format:  ## Format code with Black
	black .

format-check:  ## Check code formatting with Black
	black --check .

lint:  ## Lint code with Ruff
	ruff check .

lint-fix:  ## Lint and fix code with Ruff
	ruff check --fix .

type-check:  ## Run type checking with Mypy
	mypy .

security:  ## Run security checks with Bandit
	bandit -r . -f json -o bandit-report.json
	bandit -r .

test:  ## Run tests with pytest
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=. --cov-report=html --cov-report=term

build:  ## Build the package
	python -m build

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .mypy_cache/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -f .coverage
	rm -f bandit-report.json

all: format lint type-check security test  ## Run all checks

dev-setup: install-dev  ## Set up development environment
	@echo "Development environment setup complete!"
	@echo "Run 'make help' to see available commands."
