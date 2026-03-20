# UX Journey Scraper v0.1.0 - Initial Release

First stable release of UX Journey Scraper! 🎉

## ✨ Features

### Journey Recording
- **Playwright-based automation** - Capture multi-step user flows through websites
- **Automatic screenshots** - Visual documentation at each journey step
- **Journey metadata** - Timestamps, URLs, page titles exported as JSON

### Privacy & Ethics
- **PII blurring** - Automatically blur emails, credit cards, SSN, phone numbers
- **Robots.txt compliance** - Respect website crawling policies
- **Rate limiting** - Avoid overwhelming target servers

### UX Analysis
- **324+ guidelines** - Research-backed e-commerce UX best practices
- **Categorized analysis** - Buttons, forms, navigation, checkout, mobile
- **Severity levels** - Critical, major, and minor violations
- **Fix suggestions** - Actionable recommendations for each issue

### Accessibility
- **WCAG 2.1 validation** - Level A/AA compliance checks
- **Color contrast** - Automated contrast ratio validation
- **Alt text detection** - Screen reader compatibility checks
- **Keyboard navigation** - Accessibility support verification

### Reports
- **Interactive HTML reports** - Annotated screenshots with findings
- **Violation summaries** - Breakdown by severity
- **JSON export** - Machine-readable journey data

## 📦 Installation

```bash
# Basic installation
pip install ux-journey-scraper

# With full UX guidelines
pip install ux-journey-scraper[full]

# Install Playwright browsers
playwright install chromium
```

## 🚀 Quick Start

```bash
# Record a journey (manual navigation)
ux-journey record https://example.com

# Follow prompts to navigate through the site
# Press Enter after each step to capture screenshot
# Type 'done' when finished
```

## 🧪 Testing & Quality

- **13 unit tests** - All passing
- **CI/CD pipeline** - Automated testing on Python 3.9-3.12
- **Code coverage** - Tracked with Codecov
- **Security scanning** - Dependency and SAST analysis
- **Code quality** - Black, isort, flake8 enforced

## 📚 Documentation

- [README](https://github.com/resabh/ux-journey-scraper#readme) - Installation and usage
- [CONTRIBUTING](https://github.com/resabh/ux-journey-scraper/blob/main/CONTRIBUTING.md) - Development guide
- [CHANGELOG](https://github.com/resabh/ux-journey-scraper/blob/main/CHANGELOG.md) - Detailed release notes

## ⚠️ Known Limitations

- Integration tests require manual Playwright installation
- Full UX analysis requires optional `ecommerce-ux-guidelines` package
- Currently supports Chromium browser only (Firefox/Safari coming soon)
- English language only for guideline text

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](https://github.com/resabh/ux-journey-scraper/blob/main/CONTRIBUTING.md)

## 📄 License

MIT License - See [LICENSE](https://github.com/resabh/ux-journey-scraper/blob/main/LICENSE)

---

**Full Changelog**: https://github.com/resabh/ux-journey-scraper/blob/main/CHANGELOG.md
