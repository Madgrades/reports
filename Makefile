.PHONY: help install test lint format type-check clean validate

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	@bash scripts/install.sh

test:  ## Run tests with coverage
	pytest

lint:  ## Run linter
	ruff check .

format:  ## Format code
	ruff format .
	ruff check --fix .

type-check:  ## Run type checker
	mypy .

validate:  ## Validate that all PDFs have been processed (for CI)
	extract-tables -f csv -r --validate data csv

check: lint type-check test validate  ## Run all checks (lint, type-check, test, validate)

clean:  ## Clean temporary files
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
