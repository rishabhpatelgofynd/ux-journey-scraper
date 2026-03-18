# Changelog

All notable changes to UX Journey Scraper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### To be released in v0.1.0

## [0.1.0] - TBD

### Added
- **Journey Recording**: Capture multi-step user journeys through websites using Playwright
- **Screenshot Capture**: Automatically screenshot every step in the journey
- **PII Protection**: Blur personally identifiable information (emails, credit cards, phone numbers) in screenshots
- **UX Analysis**: Apply 324+ research-backed e-commerce UX guidelines to captured journeys
- **Accessibility Validation**: WCAG 2.1 Level A/AA compliance checks
- **Robots.txt Compliance**: Respect website robots.txt files to avoid scraping restricted areas
- **Interactive Reports**: Generate HTML reports with annotated screenshots and findings
- **CLI Tool**: Command-line interface with `ux-journey` command
- **Comprehensive Testing**: Unit tests for all core functionality
- **CI/CD Pipeline**: Automated testing and publishing via GitHub Actions
- **Documentation**: README, CONTRIBUTING, PUBLISHING guides

### Features in Detail

#### Journey Recording
- Playwright-based browser automation
- Multi-step journey capture with navigation tracking
- Automatic screenshot capture at each step
- Journey metadata (timestamps, URLs, page titles)
- Export journey data as JSON

#### UX Guidelines
- 324+ guidelines from e-commerce research
- Categorized by: buttons, forms, navigation, content, checkout, mobile, etc.
- Severity levels: critical, major, minor
- Fix suggestions for each violation
- Guideline references and sources

#### Privacy & Ethics
- PII blurring using pattern matching (emails, credit cards, SSN, phone numbers)
- Robots.txt parsing and compliance
- Rate limiting to avoid overwhelming servers
- User-agent identification
- Respects meta robots tags

#### Accessibility
- WCAG 2.1 Level A/AA checks
- Color contrast validation
- Alt text detection
- Keyboard navigation support checks
- Screen reader compatibility validation
- Focus indicator checks

#### Reports
- HTML reports with embedded screenshots
- Violation summaries with severity breakdown
- Step-by-step journey visualization
- Guideline references and explanations
- Exportable findings as JSON

### Technical Improvements
- Type hints throughout codebase
- Comprehensive error handling
- Logging with configurable verbosity
- Modular architecture for extensibility
- Memory-efficient screenshot handling
- Async/await support for performance

### Documentation
- README with installation and usage examples
- CONTRIBUTING guide for developers
- PUBLISHING guide for maintainers
- API documentation (docstrings)
- Example usage in CLI help

### Testing & Quality
- Unit tests for core functionality
- Integration tests (skipped in CI, manual for now)
- Code coverage tracking
- Linting with flake8
- Code formatting with black
- Import sorting with isort
- Pre-commit hooks

### CI/CD
- GitHub Actions workflow
- Automated testing on Python 3.9, 3.10, 3.11, 3.12
- Linting and formatting checks
- Code coverage reporting to Codecov
- Automated PyPI publishing on release
- Security scanning (dependency, SAST, secrets)

### Known Limitations
- Integration tests require manual setup (Playwright installation)
- ecommerce-ux-guidelines package is optional (full UX analysis requires it)
- Limited to Chromium browser (Firefox, Safari not yet supported)
- English language only for guideline text
- No parallel journey recording (single-threaded)

### Breaking Changes
- None (initial release)

### Deprecated
- None (initial release)

### Security
- PII blurring to prevent accidental exposure of sensitive data
- Robots.txt compliance to respect website policies
- No telemetry or data collection
- Local-only processing

### Fixed
- None (initial release)

---

## Release Notes Template (for future releases)

### [X.Y.Z] - YYYY-MM-DD

#### Added
- New features

#### Changed
- Changes to existing functionality

#### Deprecated
- Soon-to-be removed features

#### Removed
- Removed features

#### Fixed
- Bug fixes

#### Security
- Security improvements and fixes

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0   | TBD  | Initial release |

## How to Release

1. Update this CHANGELOG.md with all changes
2. Update version in `pyproject.toml` and `setup.py`
3. Run pre-publish checks: `./scripts/pre-publish-check.sh`
4. Commit: `git commit -am "Bump version to X.Y.Z"`
5. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
6. Push: `git push && git push --tags`
7. Create GitHub Release (triggers PyPI publication)

See [PUBLISHING.md](PUBLISHING.md) for detailed instructions.
