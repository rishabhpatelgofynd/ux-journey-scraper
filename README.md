# UX Journey Scraper

[![CI/CD Pipeline](https://github.com/resabh/ux-journey-scraper/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/resabh/ux-journey-scraper/actions)
[![codecov](https://codecov.io/gh/resabh/ux-journey-scraper/branch/main/graph/badge.svg)](https://codecov.io/gh/resabh/ux-journey-scraper)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Autonomous web crawler for capturing user journeys and analyzing UX patterns.**

A powerful tool for UX designers, developers, and QA teams to autonomously capture complete user flows through websites. Optionally analyze captured journeys against 324+ research-backed UX guidelines.

## 🎯 What It Does

### Core Features (v0.2.0)
- **🤖 Autonomous Crawling**: Intelligently navigates websites without manual intervention
- **🎯 Smart Element Detection**: Finds ALL clickables (buttons, links, onclick handlers, ARIA roles)
- **📸 Journey Capture**: Records complete user flows with screenshots at each step
- **🔐 Auth Support**: Handles login flows and session management
- **📋 Form Filling**: Automatically fills checkout forms (test data only)
- **🕵️ Stealth Mode**: Anti-bot detection with human-like behavior simulation
- **🔄 SPA Support**: Works with modern single-page applications
- **🛡️ Privacy-Aware**: Automatically blurs PII in screenshots

### Optional Analysis Features
- **📊 UX Guidelines**: Analyze journeys against 324+ e-commerce UX guidelines (separate command)
- **♿ Accessibility Checks**: WCAG 2.1 compliance validation (separate command)
- **📈 Interactive Reports**: HTML reports with annotated screenshots

## 🚀 Installation

### PyPI Installation (Recommended)

```bash
# Install latest version (v0.2.0 - Autonomous Crawling)
pip install ux-journey-scraper

# OR install with optional UX guidelines analysis support
pip install ux-journey-scraper[full]
```

### Installation from Source

```bash
# Clone the repository
git clone https://github.com/resabh/ux-journey-scraper.git
cd ux-journey-scraper

# Install in development mode
pip install -e .

# OR install with full UX guidelines support
pip install -e ".[full]"
```

**Note:** The `[full]` option includes `ecommerce-ux-guidelines` package for detailed UX analysis. The base installation works fully for autonomous crawling and journey capture without it.

### Post-Installation

After installation, install Playwright browsers:

```bash
playwright install chromium
```

## 📖 Quick Start

### Record a Journey

```bash
# Start recording a user journey
ux-journey record \
  --start-url https://example.com \
  --output my-journey.json

# The tool will:
# 1. Check robots.txt (asks for confirmation if needed)
# 2. Open browser
# 3. Record each page you visit
# 4. Capture screenshots
# 5. Save journey data
```

### Analyze the Journey

```bash
# Analyze recorded journey against UX guidelines
ux-journey analyze my-journey.json

# Generates:
# - my-journey-report.html (interactive report)
# - my-journey-analysis.json (detailed analysis)
# - screenshots/ (annotated images)
```

### One Command (Record + Analyze)

```bash
ux-journey run \
  --start-url https://example.com/checkout \
  --analyze \
  --output checkout-journey
```

## 💡 Use Cases

### 1. **Competitor Analysis**
Analyze competitor websites to understand UX patterns and identify opportunities.

```bash
ux-journey record --start-url https://competitor.com
```

### 2. **UX Audit**
Perform comprehensive UX audits on existing websites.

```bash
ux-journey run \
  --start-url https://mysite.com \
  --analyze \
  --output audit-results
```

### 3. **Pre-Launch Review**
Validate new features before launch.

```bash
ux-journey record \
  --start-url https://staging.mysite.com/new-feature \
  --analyze
```

### 4. **User Flow Documentation**
Document user flows with screenshots and UX validation.

```bash
ux-journey run \
  --start-url https://mysite.com/signup \
  --output user-onboarding
```

## 🛠️ Features

### Journey Recording
- ✅ Multi-step journey capture
- ✅ Automatic screenshot on each navigation
- ✅ HTML structure extraction
- ✅ Form field detection
- ✅ CTA and button analysis
- ✅ Navigation element capture

### UX Analysis
- ✅ 324+ e-commerce UX guidelines
- ✅ Page-specific validation (checkout, product, etc.)
- ✅ Priority-based issues (critical, major, minor)
- ✅ Actionable fix suggestions
- ✅ Guideline citations

### Accessibility
- ✅ WCAG 2.1 Level A/AA validation
- ✅ Color contrast analysis
- ✅ Keyboard navigation checks
- ✅ Screen reader compatibility
- ✅ ARIA attributes validation

### Privacy & Security
- ✅ PII blur in screenshots (emails, credit cards, names)
- ✅ robots.txt respect (with user confirmation)
- ✅ Rate limiting
- ✅ No data collection or tracking

### Reports
- ✅ Interactive HTML reports
- ✅ Annotated screenshots with issue markers
- ✅ JSON export for automation
- ✅ Journey flow visualization
- ✅ Issue summaries and scores

## 📋 CLI Reference

### `ux-journey record`

Record a user journey interactively.

```bash
ux-journey record [OPTIONS]

Options:
  --start-url TEXT         Starting URL (required)
  --output TEXT            Output file path (default: journey.json)
  --viewport TEXT          Viewport size (default: 1920x1080)
  --blur-pii               Blur PII in screenshots (default: true)
  --respect-robots         Check robots.txt (default: true)
  --headless              Run in headless mode (default: false)
```

### `ux-journey analyze`

Analyze a recorded journey.

```bash
ux-journey analyze [OPTIONS] JOURNEY_FILE

Options:
  --output-dir TEXT        Output directory for reports (default: ./reports)
  --format TEXT            Report format: html, json, or both (default: both)
  --guidelines TEXT        Guideline priority: all, essential, high (default: all)
```

### `ux-journey run`

Record and analyze in one command.

```bash
ux-journey run [OPTIONS]

Options:
  --start-url TEXT         Starting URL (required)
  --output TEXT            Output prefix (default: journey)
  --analyze               Run analysis after recording (default: true)
  --viewport TEXT         Viewport size (default: 1920x1080)
```

## 🔧 Python API

```python
from ux_journey_scraper import JourneyRecorder, UXAnalyzer

# Record a journey
recorder = JourneyRecorder(
    start_url="https://example.com",
    blur_pii=True,
    respect_robots=True
)

journey = await recorder.record()
journey.save("my-journey.json")

# Analyze the journey
analyzer = UXAnalyzer()
results = analyzer.analyze(journey)

# Generate report
results.generate_html_report("report.html")
results.generate_json_report("report.json")

# Access violations
for step in results.steps:
    print(f"Step {step.number}: {step.url}")
    print(f"  Issues: {len(step.violations)}")
    for violation in step.violations:
        print(f"    - {violation.title} (Guideline #{violation.guideline_id})")
```

## 📊 Sample Report Output

```
Journey Analysis Report
=======================

Journey: Checkout Flow (https://example.com)
Steps: 5
Overall Score: 72.5/100

Step 1: Homepage (/)
  Score: 85.0/100
  Issues: 3 (1 major, 2 minor)
  Screenshot: screenshots/step-001.png

Step 2: Product Listing (/products)
  Score: 78.0/100
  Issues: 5 (2 major, 3 minor)
  Screenshot: screenshots/step-002.png

Step 3: Product Detail (/products/123)
  Score: 65.0/100
  Issues: 8 (1 critical, 3 major, 4 minor)
  Screenshot: screenshots/step-003.png
  ⚠️  Critical Issue: "Add to Cart" button too small (< 44x44px)
      → Guideline #237: Touch targets must be at least 44x44px

...
```

## 🔍 How It Works

1. **Recording Phase**
   - Opens browser (Playwright)
   - Checks robots.txt (asks for confirmation if restricted)
   - Waits for user to navigate through the site
   - Captures screenshot + HTML on each navigation
   - Records journey steps in JSON

2. **Analysis Phase**
   - Loads journey data
   - Applies UX guidelines (from ecommerce-ux-guidelines)
   - Runs accessibility checks
   - Generates issue annotations
   - Blurs PII in screenshots
   - Creates interactive report

3. **Reporting Phase**
   - Generates HTML with embedded screenshots
   - Creates visual journey map
   - Exports JSON for automation
   - Annotates screenshots with issue markers

## 🧩 Integration with ecommerce-ux-guidelines

This tool depends on the `ecommerce-ux-guidelines` package for UX validation:

```python
from ecommerce_ux_guidelines import GuidelineEngine, Validator, AccessibilityValidator

# UX Journey Scraper uses these internally
engine = GuidelineEngine()
validator = Validator(engine)
a11y_validator = AccessibilityValidator(engine)
```

## 🛣️ Roadmap

### Phase 1 (Current)
- ✅ Desktop web journey recording
- ✅ UX guidelines validation
- ✅ HTML report generation
- ✅ PII blur
- ✅ robots.txt handling

### Phase 2 (Coming Soon)
- ⬜ Mobile web recording (responsive viewports)
- ⬜ Automated crawling (follow links automatically)
- ⬜ Visual journey flow diagrams
- ⬜ PDF export
- ⬜ Slack/email notifications

### Phase 3 (Future)
- ⬜ Mobile app recording (iOS/Android via Appium)
- ⬜ A/B testing comparison
- ⬜ Historical journey tracking
- ⬜ Team collaboration features
- ⬜ CI/CD integration

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Related Projects

- [ecommerce-ux-guidelines](https://github.com/rishabhpatelgofynd/BayMAAR) - 324+ research-backed UX guidelines

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/rishabhpatelgofynd/ux-journey-scraper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rishabhpatelgofynd/ux-journey-scraper/discussions)

---

**Made with ❤️ for better user experiences**
