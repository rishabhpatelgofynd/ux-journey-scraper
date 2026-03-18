.PHONY: help install install-dev test test-unit test-integration coverage lint format clean build publish

help:
	@echo "UX Journey Scraper - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install package in production mode"
	@echo "  make install-dev    Install package in development mode with dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run all tests"
	@echo "  make test-unit      Run only unit tests (skip integration tests)"
	@echo "  make test-integration  Run only integration tests"
	@echo "  make coverage       Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           Run linting checks (flake8)"
	@echo "  make format         Format code with black and isort"
	@echo "  make check          Run all quality checks (format + lint + test)"
	@echo ""
	@echo "Build & Publish:"
	@echo "  make clean          Remove build artifacts and cache files"
	@echo "  make build          Build distribution packages"
	@echo "  make publish        Publish to PyPI (requires credentials)"
	@echo ""

install:
	pip install -e .
	playwright install chromium

install-dev:
	pip install -e ".[dev]"
	playwright install chromium

test:
	pytest tests/ -v

test-unit:
	pytest tests/ -v -m "not integration"

test-integration:
	pytest tests/ -v -m integration

coverage:
	pytest tests/ --cov=ux_journey_scraper --cov-report=html --cov-report=term
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	@echo "Running flake8..."
	flake8 ux_journey_scraper/ tests/

format:
	@echo "Running black..."
	black ux_journey_scraper/ tests/
	@echo "Running isort..."
	isort ux_journey_scraper/ tests/

check: format lint test-unit
	@echo ""
	@echo "✅ All checks passed!"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

publish: build
	twine upload dist/*

# Development workflow
dev-setup: install-dev
	@echo ""
	@echo "✅ Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Activate virtual environment: source .venv/bin/activate"
	@echo "  2. Run tests: make test"
	@echo "  3. Make changes and run: make check"
	@echo ""
