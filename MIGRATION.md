# Migration Guide: v0.1.0 → v0.2.0

## Overview

UX Journey Scraper v0.2.0 introduces **autonomous crawling** with major architectural improvements. This guide helps you migrate from v0.1.0 to v0.2.0.

## What's New in v0.2.0

### Major Features

1. **Autonomous Crawling** - No manual navigation required
2. **YAML Configuration** - Config-first approach instead of CLI flags
3. **Smart Element Detection** - Finds ALL clickables (not just links/buttons)
4. **Advanced Page Readiness** - Fixes "screenshot too early" issues
5. **Form Filling** - Automatically fills checkout flows
6. **Auth Management** - Session injection for logged-in crawling
7. **Stealth Browser** - Anti-bot detection
8. **3-Layer State Dedup** - Prevents infinite loops on SPAs

### Breaking Changes

- **New primary command**: `ux-journey crawl` (replaces `record`)
- **Config file required**: `--config` flag is mandatory
- **Output format changed**: New journey structure with enhanced metadata
- **Deprecated commands**: `record` and `run` show deprecation warnings

## Migration Steps

### Step 1: Install v0.2.0

```bash
pip install --upgrade ux-journey-scraper
```

New dependencies added:
- `pyyaml>=6.0.0`
- `aiofiles>=23.0.0`

Optional for better anti-detection:
```bash
pip install patchright
patchright install chromium
```

### Step 2: Create Configuration File

**Old way (v0.1.0):**
```bash
ux-journey record https://example.com \
  --viewport 1920x1080 \
  --blur-pii \
  --output journey.json
```

**New way (v0.2.0):**

Create `scrape-config.yaml`:
```yaml
target:
  name: "Example Site"
  base_url: "https://example.com"

platforms:
  - type: web_desktop
    viewport:
      width: 1920
      height: 1080

auth:
  logged_out: true
  logged_in: false

seed_urls:
  - "https://example.com"

crawler:
  max_pages: 200
  max_depth: 8
```

Then run:
```bash
ux-journey crawl --config scrape-config.yaml
```

Use the example config as a template:
```bash
cp scrape-config.example.yaml my-config.yaml
# Edit my-config.yaml with your settings
ux-journey crawl --config my-config.yaml
```

### Step 3: Update Output Handling

**Old output (v0.1.0):**
```json
{
  "start_url": "https://example.com",
  "steps": [
    {
      "step_number": 1,
      "url": "https://example.com",
      "title": "Example",
      "screenshot_path": "screenshots/step_1.png",
      "page_data": { ... }
    }
  ]
}
```

**New output (v0.2.0):**
- Same structure, but saved to `journey_output/journey.json`
- Screenshots in `journey_output/screenshots/`
- Future versions will add `context.json` with journey graph

### Step 4: Backward Compatibility

The old commands still work but show deprecation warnings:

```bash
# These still work in v0.2.0:
ux-journey record <url> --output journey.json
ux-journey analyze journey.json
ux-journey info journey.json
ux-journey run <url>

# But you'll see:
# ⚠️  WARNING: This command is deprecated. Use 'ux-journey crawl --config <file>' for v0.2.0 features.
```

## Feature Comparison

| Feature | v0.1.0 | v0.2.0 |
|---------|--------|--------|
| **Manual navigation** | ✅ Interactive | ✅ Still available via `record` |
| **Autonomous crawling** | ❌ | ✅ NEW |
| **Configuration** | CLI flags | YAML config (required) |
| **Page readiness** | Basic (networkidle only) | Advanced (DOM stability, spinners, lazy load) |
| **Element detection** | Basic selectors | 4-strategy (semantic, ARIA, onclick, cursor) |
| **Form filling** | ❌ | ✅ Smart autocomplete-based |
| **Auth support** | ❌ | ✅ Session injection + login flows |
| **Anti-bot detection** | ❌ | ✅ Stealth browser |
| **State deduplication** | URL only | 3-layer (URL, DOM, structure) |
| **SPA support** | Limited | ✅ Full support |
| **Priority-based navigation** | ❌ | ✅ "Add to Cart" before "Learn More" |

## Configuration Examples

### Simple Static Site

```yaml
target:
  name: "Documentation Site"
  base_url: "https://docs.example.com"

platforms:
  - type: web_desktop
    viewport: {width: 1920, height: 1080}

auth:
  logged_out: true

seed_urls:
  - "https://docs.example.com"

crawler:
  max_pages: 50
  max_depth: 5
```

### E-commerce with Checkout

```yaml
target:
  name: "Example Shop"
  base_url: "https://shop.example.com"

platforms:
  - type: web_desktop
    viewport: {width: 1920, height: 1080}

auth:
  logged_out: true

seed_urls:
  - "https://shop.example.com"
  - "https://shop.example.com/products"

form_fill:
  first_name: "Test"
  last_name: "User"
  email: "test@example.com"
  phone: "+91 9876543210"
  address_line1: "123 Test St"
  city: "Mumbai"
  state: "Maharashtra"
  postal_code: "400001"
  country: "IN"
  card_number: "4111111111111111"  # Visa test card
  card_expiry_month: "12"
  card_expiry_year: "2025"
  card_cvv: "123"

crawler:
  max_pages: 100
  max_depth: 8
```

### Logged-In User Journey

```yaml
target:
  name: "Dashboard App"
  base_url: "https://app.example.com"

platforms:
  - type: web_desktop
    viewport: {width: 1920, height: 1080}

auth:
  logged_out: false
  logged_in: true
  credentials:
    username: "testuser@example.com"
    password: "testpassword123"
  login_url: "https://app.example.com/login"
  login_success_indicator: "/dashboard"
  session_file: "session.json"

seed_urls:
  - "https://app.example.com/dashboard"

crawler:
  max_pages: 50
```

## Common Issues

### Issue: "Config file not found"

**Solution:** Provide absolute path or ensure file is in current directory.
```bash
ux-journey crawl --config ./scrape-config.yaml
```

### Issue: "Invalid platform type"

**Solution:** Use one of: `web_desktop`, `web_mobile`, `web_tablet`

### Issue: "Test card validation failed"

**Solution:** Only these test cards are allowed:
- Visa: `4111111111111111`
- Mastercard: `5555555555554444`
- Amex: `378282246310005`

### Issue: "Authentication failed"

**Solution:** Verify:
- `login_url` is correct
- `credentials` are valid
- `login_success_indicator` matches post-login state

## Getting Help

- **Documentation**: See README.md for full v0.2.0 documentation
- **Examples**: Check `scrape-config.example.yaml`
- **Issues**: Report at https://github.com/resabh/ux-journey-scraper/issues

## Rollback to v0.1.0

If you need to rollback:
```bash
pip install ux-journey-scraper==0.1.0
```

## What's Next

Planned for v0.3.0:
- Context file output (journey graph + parity matrix)
- Multi-platform parallel crawling
- CAPTCHA detection improvements
- iOS/Android native app support
