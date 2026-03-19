# CI/CD Pipeline Setup

## Overview

The UX Journey Scraper project has a comprehensive CI/CD pipeline that automatically validates code quality, runs tests, and publishes releases to PyPI.

## Pipeline Components

### 1. Linting (`lint` job)
- **Black** - Code formatting check (line length: 100)
- **isort** - Import sorting validation
- **flake8** - Python linting and style checks

**Triggers:** All pushes and pull requests to `main` or `develop`

### 2. Testing (`test` job)
- Runs on Python versions: 3.9, 3.10, 3.11, 3.12
- Executes unit tests (non-integration tests)
- Executes integration tests (continue-on-error for dependencies)
- Matrix strategy ensures compatibility across Python versions

**Triggers:** All pushes and pull requests to `main` or `develop`

### 3. Coverage (`coverage` job)
- Generates code coverage reports
- Uploads to Codecov for tracking
- Targets 70% minimum coverage
- Generates XML and terminal reports

**Triggers:** All pushes and pull requests to `main` or `develop`

### 4. Build (`build` job)
- Builds Python distribution packages (wheel + sdist)
- Validates packages with `twine check`
- Uploads build artifacts (7-day retention)
- Depends on: `lint` and `test` jobs passing

**Triggers:** All pushes and pull requests to `main` or `develop`

### 5. Publish (`publish` job)
- Publishes to PyPI using trusted publishing
- Only runs on GitHub releases
- Uses PyPI's trusted publisher workflow (no API tokens needed)
- Depends on: `lint`, `test`, and `build` jobs passing

**Triggers:** Only when a GitHub release is published

## Local Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Or use Makefile
make install-dev
```

### Pre-commit Checks

Before committing, run:

```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test-unit

# Or run all checks
make check
```

### Running Tests Locally

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# With coverage report
make coverage
```

## Configuration Files

### `.github/workflows/ci.yml`
Main CI/CD workflow definition

### `pyproject.toml`
- Build system configuration
- Black, isort, pytest, coverage settings
- Package metadata

### `.flake8`
Flake8 linting configuration

### `.codecov.yml`
Code coverage thresholds and reporting

### `Makefile`
Development convenience commands

## Workflow Triggers

| Event | Branches | Jobs |
|-------|----------|------|
| Push | `main`, `develop` | lint, test, coverage, build |
| Pull Request | `main`, `develop` | lint, test, coverage, build |
| Release Published | any | lint, test, coverage, build, publish |

## Branch Protection (Recommended)

For production use, configure branch protection on `main`:

1. Require status checks to pass:
   - `Lint Code`
   - `Test Python 3.9`, `3.10`, `3.11`, `3.12`
   - `Code Coverage`
   - `Build Package`

2. Require pull request reviews

3. Require branches to be up to date

## PyPI Publishing Setup

### Prerequisites

1. **Create PyPI Account:** https://pypi.org/account/register/

2. **Configure Trusted Publishing:**
   - Go to PyPI → Account → Publishing
   - Add GitHub as trusted publisher
   - Owner: `resabh`
   - Repository: `ux-journey-scraper`
   - Workflow: `ci.yml`
   - Environment: (leave empty)

3. **Create GitHub Release:**
   ```bash
   # Tag version
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0

   # Create GitHub Release
   gh release create v0.1.0 --title "v0.1.0" --notes "Release notes"
   ```

The `publish` job will automatically upload to PyPI when a release is created.

## Status Badges

Add to README.md:

```markdown
[![CI/CD Pipeline](https://github.com/resabh/ux-journey-scraper/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/resabh/ux-journey-scraper/actions)
[![codecov](https://codecov.io/gh/resabh/ux-journey-scraper/branch/main/graph/badge.svg)](https://codecov.io/gh/resabh/ux-journey-scraper)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
```

## Troubleshooting

### Tests Failing Locally but Pass in CI
- Ensure you're using the same Python version
- Check virtual environment isolation
- Verify all dev dependencies are installed

### Linting Failures
- Run `make format` to auto-fix formatting issues
- Check `.flake8` for ignored rules
- Ensure isort profile matches black

### Coverage Drops Below Threshold
- Add tests for new functionality
- Check `.codecov.yml` for coverage targets
- Review coverage report: `make coverage`

### PyPI Publishing Fails
- Verify trusted publisher configuration
- Check version number is not already published
- Ensure release is properly created on GitHub

## Cost and Performance

- **Cost:** Free (GitHub Actions free tier)
- **Runtime:** ~3-5 minutes per run
- **Matrix Testing:** Runs in parallel across Python versions
- **Artifacts:** Retained for 7 days

## Security

- **No secrets required** - Uses trusted publishing
- **Dependabot enabled** - Automatic dependency updates
- **CodeQL scanning** - Available in `.github/workflows/security.yml` (in main BayMAAR project)
- **Gitleaks** - Secret scanning

## Next Steps

1. ✅ Configure branch protection rules
2. ✅ Set up PyPI trusted publishing
3. ✅ Create first GitHub release
4. ✅ Monitor code coverage trends
5. ✅ Add Dependabot configuration
