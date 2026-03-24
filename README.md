# UX Journey Scraper

[![CI/CD Pipeline](https://github.com/resabh/ux-journey-scraper/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/resabh/ux-journey-scraper/actions)
[![codecov](https://codecov.io/gh/resabh/ux-journey-scraper/branch/main/graph/badge.svg)](https://codecov.io/gh/resabh/ux-journey-scraper)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Autonomous web crawler for capturing user journeys.**

A powerful tool for UX designers, developers, and QA teams to autonomously capture complete user flows through websites.

## 🎯 What It Does

### Core Features (v0.5.0)

- **🤖 Autonomous Crawling**: Intelligently navigates websites without manual intervention
- **🎯 Smart Element Detection**: Finds ALL clickables (buttons, links, onclick handlers, ARIA roles)
- **📸 Journey Capture**: Records complete user flows with screenshots at each step
- **📱 Multi-Platform**: Crawls desktop, mobile, tablet, and native apps in a single run
- **📲 Native App Testing**: Android (UiAutomator2) and iOS (XCUITest) via Appium
- **🔐 Auth Support**: Handles login flows and session management
- **📋 Form Filling**: Automatically fills checkout forms (test data only)
- **🕵️ Stealth Mode**: Anti-bot detection with human-like behavior simulation
- **🔄 SPA Support**: Works with modern single-page applications
- **🛡️ Privacy-Aware**: Automatically blurs PII in screenshots

### Platform Support

| Platform | Type | Status | Notes |
|---|---|---|---|
| Web Desktop | `web_desktop` | ✅ | Playwright / Chromium |
| Web Mobile | `web_mobile` | ✅ | Playwright with mobile UA + viewport |
| Web Tablet | `web_tablet` | ✅ | Playwright with tablet UA + viewport |
| Android Native | `native_android` | ✅ | Appium UiAutomator2; requires `[native]` extras |
| iOS Native | `native_ios` | ✅ | Appium XCUITest; macOS only; requires `[native]` extras |
| WebView wrapper | auto-detected | ✅ | Ionic/Capacitor/Cordova — switches to DOM context |
| Flutter (semantics on) | auto-detected | ✅ | Accessibility tree available |
| Flutter (semantics off) | auto-detected | ✅ | Screenshot-only scroll mode |

## 🚀 Installation

### PyPI Installation (Recommended)

```bash
# Install latest version
pip install ux-journey-scraper

# With native Android/iOS app testing support
pip install 'ux-journey-scraper[native]'
```

### Installation from Source

```bash
# Clone the repository
git clone https://github.com/resabh/ux-journey-scraper.git
cd ux-journey-scraper

# Install in development mode
pip install -e .

# With native app testing extras
pip install -e ".[native]"
```

### Post-Installation

After installation, install Playwright browsers:

```bash
playwright install chromium
```

For native app testing, also install Appium drivers:

```bash
# Install Appium (once)
npm install -g appium

# Install platform drivers
appium driver install uiautomator2   # Android
appium driver install xcuitest       # iOS (macOS only)

# Start Appium server
appium --port 4723
```

## 📖 Quick Start

### Autonomous Crawl (v0.3.0)

```bash
# Create a configuration file (see scrape-config.example.yaml)
ux-journey crawl --config scrape-config.yaml --output-dir journey_output/

# The tool will:
# 1. Check robots.txt (asks for confirmation if needed)
# 2. Autonomously navigate through the site
# 3. Capture screenshots at each step
# 4. Record complete user journey
# 5. Save journey data as JSON + screenshots
```

### Manual Recording (Deprecated)

```bash
# Manually record a journey (interactive mode)
ux-journey record \
  --start-url https://example.com \
  --output my-journey.json

# Note: Use 'crawl' for autonomous navigation
```

## 💡 Use Cases

### 1. **Competitor Analysis**

Capture competitor websites to understand user flows and patterns.

```bash
ux-journey crawl --config competitor-config.yaml --output-dir competitor_journey/
```

### 2. **User Flow Documentation**

Document user flows with screenshots for design/QA teams.

```bash
ux-journey crawl --config mysite-config.yaml --output-dir user_flows/
```

### 3. **Pre-Launch Testing**

Capture staging sites before launch.

```bash
ux-journey crawl --config staging-config.yaml --output-dir staging_test/
```

### 4. **QA Automation**

Automated journey capture for regression testing.

```bash
ux-journey crawl --config qa-config.yaml --output-dir qa_snapshots/
```

## 🛠️ Features

### Journey Recording

- ✅ Autonomous crawling with priority queue
- ✅ Multi-step journey capture
- ✅ Automatic screenshot on each navigation
- ✅ HTML structure extraction
- ✅ Form field detection and auto-fill
- ✅ CTA and button analysis
- ✅ Navigation element capture
- ✅ Session management and auth support

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

## 🖥️ Platform Support

| Platform | Type | Emulation |
|---|---|---|
| Desktop (1920×1080) | `web_desktop` | Chromium, Windows UA |
| Mobile iPhone 14 Pro (390×844) | `web_mobile` | Touch events, iPhone UA, 2× DPR |
| Tablet iPad Air (820×1180) | `web_tablet` | Touch events, iPad UA, 2× DPR |
| Native Android app | `native_android` | Phase 2 (v0.5.0, requires Appium) |
| Native iOS app | `native_ios` | Phase 2 (v0.5.0, requires Appium + Xcode) |

All web platform types are **browser-based emulation** via Playwright viewport + UA spoofing — no real devices required.

### Multi-Platform Crawling

Specify multiple platforms in your config to crawl all of them in one run:

```yaml
platforms:
  - type: web_desktop
    viewport: { width: 1920, height: 1080 }
    locale: "en-IN"
    timezone_id: "Asia/Kolkata"

  - type: web_mobile        # iPhone 14 Pro
    viewport: { width: 390, height: 844 }
    locale: "en-IN"
    timezone_id: "Asia/Kolkata"

  - type: web_tablet        # iPad Air
    viewport: { width: 820, height: 1180 }
    locale: "en-IN"
    timezone_id: "Asia/Kolkata"
```

Output is organized per platform:

```
journey_output/
  web_desktop/
    journey.json
    screenshots/
  web_mobile/
    journey.json
    screenshots/
  web_tablet/
    journey.json
    screenshots/
```

---

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

## 🔧 Python API

```python
from ux_journey_scraper import JourneyRecorder, Journey
from ux_journey_scraper.config import ScrapeConfig
from ux_journey_scraper.core import AutonomousCrawler

# Option 1: Autonomous crawling with config
config = ScrapeConfig.load("scrape-config.yaml")
crawler = AutonomousCrawler(config=config, output_dir="journey_output/")
journey = await crawler.crawl()

# Option 2: Manual recording (deprecated)
recorder = JourneyRecorder(
    start_url="https://example.com",
    blur_pii=True,
    respect_robots=True
)
journey = await recorder.record()
journey.save("my-journey.json")

# Load existing journey
journey = Journey.load("journey.json")

# Access journey data
for step in journey.steps:
    print(f"Step {step.step_number}: {step.title}")
    print(f"  URL: {step.url}")
    print(f"  Screenshot: {step.screenshot_path}")
```

## 📊 Sample Journey Output

```json
{
  "start_url": "https://example.com",
  "start_time": "2026-03-19T12:00:00Z",
  "end_time": "2026-03-19T12:05:30Z",
  "viewport": [1920, 1080],
  "steps": [
    {
      "step_number": 1,
      "url": "https://example.com",
      "title": "Homepage",
      "screenshot_path": "screenshots/step-001.png",
      "html_snapshot": "...",
      "page_data": {
        "forms": [...],
        "buttons": [...],
        "links": [...]
      }
    },
    ...
  ]
}
```

## 🔍 How It Works

1. **Configuration**
   - YAML config defines seed URLs, auth, form fill settings
   - Priority queue manages navigation strategy

2. **Autonomous Crawling**
   - Launches stealth browser (anti-bot detection)
   - Navigates autonomously using priority queue
   - Finds ALL clickables (buttons, links, ARIA roles, onclick handlers)
   - Handles login flows and session management
   - Fills forms with test data (payment safeguards)

3. **Capture**
   - Waits for page readiness (DOM stable, no spinners, lazy-load complete)
   - Captures screenshot + HTML at each step
   - Blurs PII automatically
   - Records all page data (forms, buttons, links)

4. **Output**
   - Saves journey JSON with all steps
   - Screenshots folder with PII blurred
   - Complete DOM snapshots for analysis

## 🛣️ Roadmap

### v0.4.0 (Current) - Multi-Platform Web Crawling

- ✅ Autonomous crawling with priority queue
- ✅ Desktop web journey recording
- ✅ Mobile viewport emulation (iPhone 14 Pro)
- ✅ Tablet viewport emulation (iPad Air)
- ✅ Multi-platform crawl in a single run (per-platform output dirs)
- ✅ Smart element detection (4 strategies)
- ✅ Auth support and session management
- ✅ Form auto-fill with safeguards
- ✅ PII blur in screenshots
- ✅ robots.txt handling
- ✅ Stealth mode (anti-bot detection)

### v0.5.0 (Next) - Native App Testing (Appium)

- ⬜ Native Android app crawling (UiAutomator2)
- ⬜ Native iOS app crawling (XCUITest, macOS only)
- ⬜ Appium session setup and element detection via accessibility tree
- ⬜ Integration with `platform_discovery.py` (bundle ID / package name lookup)

  **Requirements**: `pip install Appium-Python-Client`, Android SDK + ADB or Xcode + iOS Simulator

### Future Enhancements

- ⬜ Multi-page site mapping
- ⬜ CAPTCHA handling improvements
- ⬜ Visual regression detection
- ⬜ Performance metrics capture
- ⬜ CI/CD integration

### Analysis Features → Moved to BayMAAR

- UX guidelines analysis is now in the separate BayMAAR Analysis Engine (private)
- This package remains a pure journey capture tool

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
