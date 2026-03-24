# Phase 2 Plan: Native & Cross-Platform Mobile App Testing

## ux-journey-scraper v0.5.0 Roadmap

> **Context**: Phase 1 (v0.4.0) ships web emulation — Playwright + viewport/UA spoofing for desktop, mobile, and tablet.
> Phase 2 covers real app testing: apps installed on a device or emulator.

---

## Research Finding: The Mobile App Landscape

Most companies do not build one type of app. The market splits into roughly four buckets:

| App Type | Market Share (est. 2024) | Key Companies |
|---|---|---|
| Pure native (Swift/Kotlin) | ~35–45% of professional apps | Apple, Google, Snapchat, Uber, Airbnb, TikTok, Spotify, Twitter/X |
| React Native | ~8–9% of developers | Meta/Facebook, Shopify, Discord, Walmart, Bloomberg, Tesla |
| Flutter | ~9–10% of developers | Google Pay, eBay Motors, BMW, Nubank, Alibaba (Xianyu) |
| Ionic / Capacitor (WebView) | ~5–6% of developers | MarketWatch, enterprise B2B apps, Burger King regional apps |

**The key insight the user raised is correct**: A large segment of apps — primarily Ionic/Capacitor and some React Native hybrid approaches — use a web wrapper that renders HTML/CSS/JS inside a native shell. For those apps, the UI is nearly identical to a web experience, and only the interaction model (touch gestures, OS-level navigation) differs meaningfully.

Pure native, React Native (new arch), and Flutter draw their UI through native or custom rendering engines with no accessible DOM. Those require a completely different testing strategy.

---

## Why This Matters for ux-journey-scraper

Currently `app_architecture_detector.py` and `platform_discovery.py` exist as stubs. They do the right thing — detect what kind of app you're dealing with — but the detection informs which **crawling strategy** to use. Different app types need different tools:

| App Type | Rendering Engine | Playwright works? | Right tool |
|---|---|---|---|
| Web (Phase 1, done) | Browser | Yes — fully | Playwright |
| PWA | Browser (in-app) | Yes — fully | Playwright (already works) |
| Ionic / Capacitor | WKWebView / Android WebView | Yes — via WebView context | Appium → switch to `WEBVIEW` context → Playwright-like automation |
| React Native (old arch) | Native components via JS bridge | No | Appium (UIAutomator2 / XCTest driver) |
| React Native (new arch / Fabric) | Native components via JSI | No | Appium, or Detox (better for RN) |
| Flutter | Custom canvas (Skia / Impeller) | No | Appium Flutter Driver, or Maestro |
| Pure native iOS | UIKit / SwiftUI | No | Appium (XCTest driver), or XCUITest |
| Pure native Android | Views / Jetpack Compose | No | Appium (UIAutomator2), or Espresso |

---

## Architecture Decision: Detection-First Strategy

The `AppiumCrawler` must not assume it knows what kind of app it is targeting. It should:

1. **Detect** the app type (static analysis of the APK/IPA, or runtime context detection)
2. **Route** to the correct crawling strategy
3. **Crawl** using that strategy's primitives

This maps directly onto what `app_architecture_detector.py` should become: not a stub, but the **entry point** for all Phase 2 crawling.

---

## Detection Methods (from Research)

### Static Analysis (before launching the app)

**Android APK:**

```
unzip app.apk → inspect contents:
  lib/arm64-v8a/libflutter.so        → Flutter
  assets/index.android.bundle        → React Native
  assets/public/index.html           → Ionic / Capacitor
  assets/www/cordova.js              → Cordova
  (none of the above)                → Pure native
```

**iOS IPA:**

```
unzip app.ipa → inspect Payload/App.app/:
  Frameworks/Flutter.framework       → Flutter
  main.jsbundle                      → React Native
  public/index.html                  → Ionic / Capacitor
  www/cordova.js                     → Cordova
  (none of the above)                → Pure native
```

### Runtime Detection (after launching with Appium)

```python
# Check available WebView contexts
contexts = driver.contexts
# ['NATIVE_APP']                         → native / Flutter / RN
# ['NATIVE_APP', 'WEBVIEW_com.example']  → Ionic / Capacitor / hybrid

# For Flutter specifically: UI elements show as XCUIElementTypeOther
# with synthetic labels instead of real UIAccessibility types
```

### `app_architecture_detector.py` — what it should become

```python
class AppArchitectureDetector:
    def detect_from_package(self, apk_or_ipa_path: str) -> AppType:
        """Static binary analysis."""
        ...

    def detect_at_runtime(self, appium_driver) -> AppType:
        """Runtime context/element heuristics."""
        ...

class AppType(Enum):
    NATIVE_IOS = "native_ios"
    NATIVE_ANDROID = "native_android"
    REACT_NATIVE = "react_native"
    FLUTTER = "flutter"
    IONIC_CAPACITOR = "ionic_capacitor"
    CORDOVA = "cordova"
    PWA = "pwa"
```

---

## Phase 2 Implementation Plan (v0.5.0)

### Phase 2a — Wrapper Apps: Ionic / Capacitor (lowest effort, highest payoff)

**Why first**: Ionic/Capacitor apps are WebViews. Once Appium launches the app and switches context to the WebView, the automation is nearly identical to Phase 1 Playwright automation. Most of the existing code (`element_intelligence.py`, `form_filler.py`, `page_readiness.py`) can be reused.

**What needs building:**

- Appium session setup (Android: `UIAutomator2` driver, iOS: `XCTest` driver)
- Launch app → detect WebView context → switch to it
- Thin adapter that wraps Appium's WebView as a Playwright-compatible interface
- Or: use `appium-webdriverio` / CDP attach to avoid writing a new abstraction

**Touch point differences to handle:**

- `swipe` to scroll (replace `scrollIntoView` with touch drag)
- `long press` for context menus
- `pull-to-refresh` if the app uses it as a navigation gesture

**Effort**: Low–Medium. ~2–3 weeks of build time.

---

### Phase 2b — React Native (medium effort)

React Native (both old and new arch) exposes a **native accessibility tree**, so Appium's UIAutomator2 and XCTest drivers work. Elements are real native views.

**What needs building:**

- `ReactNativeCrawler` class (extends or mirrors `AutonomousCrawler` interface)
- Appium session setup with appropriate capabilities
- Element detection via accessibility tree instead of DOM queries
- Gesture primitives: swipe, scroll, long press, back-swipe (iOS edge)
- Screenshot capture via Appium (`driver.get_screenshot_as_base64()`)
- State deduplication: screenshot hash + element tree hash (no URL to deduplicate on)

**Key difference from web crawling:**

- No URL to track state — must use screen content hashing
- Navigation is gesture-based (back swipe, bottom tab tap, drawer open) not URL-based
- Deep links can be used as seed "URLs" (`app://screen/name`)

**Tooling choice**: Appium is the pragmatic choice for integration into this Python codebase. Detox (Node.js) would be better for RN but requires a completely different language runtime.

**Effort**: Medium. ~4–6 weeks.

---

### Phase 2c — Flutter (hardest, most constrained)

Flutter draws its own pixels. There is no UIKit/Android View hierarchy. Appium's standard drivers see nothing meaningful.

**Options:**

1. **Appium Flutter Driver**: Uses Flutter's semantics bridge (accessibility must be enabled in the app build). Works but requires a debug/profile build of the app.
2. **Maestro** (framework-agnostic, YAML-based): Interacts with accessibility tree on native/RN, and Flutter semantics on Flutter. Becoming the community standard for Flutter testing.
3. **flutter_test / integration_test**: Official Flutter testing packages, but they require embedding test code inside the app — not compatible with external black-box crawling.

**Recommendation**: For Phase 2c, wrap **Maestro** via subprocess calls rather than building from scratch. Maestro's YAML DSL can be generated programmatically.

```python
# Generate Maestro flow YAML:
flow = {
    "appId": "com.example.app",
    "---": [
        {"launchApp": {}},
        {"tapOn": {"text": "Sign In"}},
        {"takeScreenshot": "step-001"},
    ]
}
```

**Effort**: Medium–High. ~4–6 weeks (Maestro wrapper) or longer (native Appium Flutter driver).

---

### Phase 2d — Pure Native (iOS / Android)

Appium's standard XCTest (iOS) and UIAutomator2 (Android) drivers work for pure native apps. Same approach as React Native minus the JS-layer complications.

**What's unique:**

- Platform-specific interaction patterns (iOS: navigation controller back button; Android: hardware back key)
- OS-level gestures that cannot be blocked (swipe from screen edge to go back on iOS)
- Permission dialogs (camera, location, notifications) interrupt flow — must be dismissed

**Effort**: Medium. Can share the `ReactNativeCrawler` infrastructure. Platform-specific gesture handling adds effort.

---

## Touch Interaction Differences (Web vs. Mobile — What Changes)

The user's original question was specifically about the interaction difference between web and native mobile. Here is the complete delta:

| Interaction | Web (Phase 1) | Native mobile (Phase 2) |
|---|---|---|
| Primary navigation | Click link / `href` | Tap native element / swipe between screens |
| Scroll | `scrollIntoView` / wheel events | Touch scroll with momentum (different feel) |
| Back navigation | `history.back()` | Edge swipe (iOS) / hardware back (Android) |
| Pull-to-refresh | Not a web standard | Drag list past top boundary |
| Swipe-to-dismiss / delete | Rare (CSS only) | Core pattern (iOS swipe-left on list item) |
| Long press | `contextmenu` event | Platform context menu / drag start |
| Pinch-to-zoom | CSS + pointer events | OS-level gesture (pinch spread/contract) |
| Bottom sheet reveal | CSS animation | Native drag gesture on handle |
| Tab bar navigation | Click `<a>` | Tap native tab bar item |
| Haptic feedback | Web Vibration API (rarely used in UX) | Motor feedback on every interaction |
| Deep link entry | URL navigation | `app://scheme/path` intent/universal link |

For automated testing, Appium handles all of these via `W3C Actions` (touch events) and platform-specific gesture commands.

---

## What Already Exists in the Codebase (Keep, Expand)

| File | Current state | Phase 2 role |
|---|---|---|
| `core/app_architecture_detector.py` | Stub — hardcoded heuristics | Expand to full binary + runtime detector |
| `core/platform_discovery.py` | Stub — hardcoded lookup tables, uses `aiohttp` | Expand to real App Store / Play Store API calls for bundle ID / package name lookup |
| `config/scrape_config.py` | Supports `PlatformConfig` with `type` field | Add `native_android` and `native_ios` types; add `app_package`, `app_activity`, `bundle_id` fields |

---

## New Files to Build (Phase 2)

```
ux_journey_scraper/
  core/
    appium_session.py          # Appium driver setup, capabilities builder
    appium_crawler.py          # Main crawler (mirrors AutonomousCrawler interface)
    native_element_detector.py # Accessibility tree traversal (replaces element_intelligence for native)
    gesture_engine.py          # Swipe, long press, pinch, pull-to-refresh primitives
    mobile_state_registry.py   # Screen deduplication by screenshot hash + element hash (no URLs)
    maestro_runner.py          # Optional: Maestro subprocess wrapper for Flutter
```

---

## Configuration Schema (Phase 2 additions to `scrape-config.yaml`)

```yaml
platforms:
  # Phase 1 (already works)
  - type: web_desktop
    viewport: { width: 1920, height: 1080 }

  - type: web_mobile
    viewport: { width: 390, height: 844 }

  # Phase 2 (native apps)
  - type: native_android
    app_package: "com.example.app"
    app_activity: ".MainActivity"
    apk_path: "./build/app-release.apk"   # optional: install from local file
    appium_server: "http://localhost:4723"
    avd_name: "Pixel_7_API_34"            # optional: start emulator

  - type: native_ios
    bundle_id: "com.example.app"
    ipa_path: "./build/app.ipa"           # optional: install from local file
    appium_server: "http://localhost:4723"
    simulator_udid: "XXXXXXXX-XXXX-..."   # optional: specific simulator
```

---

## Dependencies (Phase 2)

```toml
# Add to pyproject.toml [project.optional-dependencies]
native = [
    "Appium-Python-Client>=3.1.0",
]
```

Keep as optional — most users only need Phase 1 web crawling. Native testing is a deliberate opt-in:

```bash
pip install ux-journey-scraper[native]
```

**External requirements (not pip-installable):**

- **Appium server**: `npm install -g appium && appium driver install uiautomator2 xcuitest`
- **Android**: Android SDK, ADB, AVD Manager (or a real device)
- **iOS**: Xcode, iOS Simulator (macOS only), valid provisioning profile for real devices
- **Flutter (optional)**: Appium Flutter driver: `appium driver install flutter`
- **Maestro (optional)**: `curl -Ls "https://get.maestro.mobile.dev" | bash`

---

## Recommended Rollout Order (within v0.5.0)

1. **Expand `app_architecture_detector.py`** — static binary detection (APK/IPA inspection). This is pure Python with `zipfile` — no Appium required. Ship this first as it unblocks all downstream work.

2. **Appium session setup** (`appium_session.py`) — capabilities builder for Android and iOS. Validates that Appium + drivers are installed before attempting a crawl.

3. **Ionic/Capacitor crawler** — easiest win. Launch via Appium, switch to WebView context, reuse existing web automation logic. Demonstrates the architecture working end-to-end.

4. **React Native / Native crawler** — `native_element_detector.py` + `gesture_engine.py`. Shared between RN and pure native since both expose the native accessibility tree.

5. **Flutter** — last, because it requires a separate driver and the detection/interaction model is most different. Evaluate Maestro as the strategy rather than Appium Flutter Driver.

---

## What Does NOT Change Between Web and Native (Reuse as-is)

- `screenshot_manager.py` — screenshot capture is already file-based; Appium returns base64 PNG, same format
- `compliance_reporter.py` — report generation is downstream of captured data; platform-agnostic
- `journey_recorder.py` / `Journey` / `JourneyStep` — the output schema stays the same
- `form_filler.py` — logic for what to fill is the same; only the _how_ changes (native text input vs. web `<input>`)
- Auth flow logic — same concept, different element interaction primitives

---

## Summary

| Phase | Scope | Key blocker |
|---|---|---|
| 1 (done, v0.4.0) | Web emulation: desktop + mobile + tablet | None — shipped |
| 2a (v0.5.0 first) | Ionic/Capacitor (WebView wrapper apps) | Appium setup + WebView context switching |
| 2b (v0.5.0) | React Native + pure native | Appium + native element detection |
| 2c (v0.5.0 stretch) | Flutter | Appium Flutter Driver or Maestro integration |
| 3 (future) | Real device farms (BrowserStack, SauceLabs) | Cloud API integration + provisioning |
