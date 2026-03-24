# Contributing to UX Journey Scraper

Thank you for your interest in contributing to UX Journey Scraper! This document provides guidelines and instructions for contributing.

## ⚠️ Privacy & Scope

**IMPORTANT**: UX Journey Scraper is a **public package** (MIT License).

### What Belongs Here

✅ **Allowed**:

- Journey capture functionality
- Screenshot handling
- Browser automation
- Generic UX utilities
- Test data and mock examples
- Public documentation

❌ **NOT Allowed**:

- Proprietary UX guidelines or research data
- Integration with private analysis engines
- Hard-coded paths to private data
- Baymard Institute proprietary content

### Package Scope

This package is focused on **journey capture only**. UX analysis features have been moved to a separate private repository (BayMAAR).

**If you want to add UX analysis features**, please understand:

- This package captures journeys (screenshots + data)
- Analysis happens in a separate private system
- Integration is via data files (journey.json), not code coupling

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- pip

### Setting Up Development Environment

1. **Clone the repository:**

   ```bash
   git clone https://github.com/resabh/ux-journey-scraper.git
   cd ux-journey-scraper
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies:**

   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Playwright browsers:**

   ```bash
   playwright install chromium
   ```

## Development Workflow

### Code Quality Standards

We use several tools to ensure code quality:

- **Black** - Code formatting (line length: 100)
- **isort** - Import sorting
- **flake8** - Linting
- **pytest** - Testing

### Before Committing

Run these commands before committing your changes:

```bash
# 1. Privacy check (CRITICAL)
git status  # Look for: no proprietary data files
git diff    # Review: no hard-coded private paths

# 2. Format code
black ux_journey_scraper/ tests/

# 3. Sort imports
isort ux_journey_scraper/ tests/

# 4. Run linting
flake8 ux_journey_scraper/ tests/

# 5. Run tests
pytest tests/ -v
```

Or use this one-liner (after privacy check):

```bash
black . && isort . && flake8 . && pytest tests/
```

**Privacy Checklist** (run before every commit):

- [ ] No proprietary data files added (*.json with guidelines, etc.)
- [ ] No hard-coded paths to private data (`.local/`, `baymard_backup/`, etc.)
- [ ] No integration code that requires private dependencies
- [ ] Package remains standalone (no private imports)

### Running Tests

```bash
# Run all tests
pytest tests/

# Run only unit tests (skip integration tests)
pytest tests/ -m "not integration"

# Run with coverage
pytest tests/ --cov=ux_journey_scraper --cov-report=html

# Run specific test file
pytest tests/test_recorder.py -v
```

### Code Coverage

We aim for at least 70% code coverage. To check coverage:

```bash
pytest tests/ --cov=ux_journey_scraper --cov-report=term --cov-report=html
```

View the HTML report:

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## CI/CD Pipeline

Our CI/CD pipeline runs automatically on every push and pull request.

### Pipeline Stages

1. **Lint** - Code quality checks (Black, isort, flake8)
2. **Test** - Run tests on Python 3.9, 3.10, 3.11, 3.12
3. **Coverage** - Generate code coverage reports
4. **Build** - Build Python package
5. **Publish** - Publish to PyPI (on release only)

### Triggering CI

The CI pipeline runs on:

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Published releases

### Viewing CI Results

Check the "Actions" tab on GitHub to view CI results for your pull request.

## Pull Request Process

1. **Create a feature branch:**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clear, concise commit messages
   - Add tests for new functionality
   - Update documentation as needed

3. **Ensure all checks pass:**

   ```bash
   black . && isort . && flake8 . && pytest tests/
   ```

4. **Push your branch:**

   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request:**
   - Provide a clear description of the changes
   - Reference any related issues
   - Wait for CI checks to pass
   - Request review from maintainers

## Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Maximum line length: 100 characters

### Documentation

- Update README.md if adding new features
- Add docstrings to new functions and classes
- Include examples in docstrings where helpful

### Testing

- Write unit tests for all new functionality
- Maintain or improve code coverage
- Use descriptive test names
- Group related tests in classes

### Example Test Structure

```python
class TestFeatureName:
    """Test the feature functionality"""

    def test_basic_functionality(self):
        """Test that the feature works in basic cases"""
        # Arrange
        input_data = "test"

        # Act
        result = your_function(input_data)

        # Assert
        assert result == expected_output
```

## Reporting Issues

When reporting issues, please include:

1. **Description** - Clear description of the issue
2. **Steps to Reproduce** - How to reproduce the issue
3. **Expected Behavior** - What you expected to happen
4. **Actual Behavior** - What actually happened
5. **Environment** - Python version, OS, package version
6. **Logs/Screenshots** - Any relevant logs or screenshots

## Release Process

Releases are managed by maintainers. The process:

1. Update version in `pyproject.toml` and `setup.py`
2. Update CHANGELOG.md
3. Create a Git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
4. Push tag: `git push origin v0.1.0`
5. Create GitHub Release (triggers PyPI publication)

## Questions?

If you have questions about contributing, please open an issue with the "question" label.

## License

By contributing to UX Journey Scraper, you agree that your contributions will be licensed under the MIT License.
