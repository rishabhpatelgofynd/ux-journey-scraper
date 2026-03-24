"""
App Architecture Detection Demo

Demonstrates detection of native, WebView, or hybrid mobile app architecture.
Requires Appium setup to run with real apps.
"""

import asyncio


async def demo_architecture_detection():
    """
    Demo: Detect app architecture (requires Appium).
    """
    print("=" * 80)
    print("APP ARCHITECTURE DETECTION DEMO")
    print("=" * 80)
    print()

    print("⚠️  This demo requires Appium setup with a real app")
    print()

    # Try to import Appium
    try:
        from appium import webdriver
        from appium.options.android import UiAutomator2Options
        from ux_journey_scraper.core import AppArchitectureDetector

        print("✓ Appium available - running live demo")
        print()

        # Example configuration (user would customize)
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = "Android Emulator"
        options.app_package = "com.example.ecommerce"  # Replace with real package
        options.app_activity = ".MainActivity"

        print("📱 Connecting to app...")
        print(f"   Package: {options.app_package}")
        print()

        try:
            # Connect to Appium server
            driver = webdriver.Remote("http://localhost:4723", options=options)

            # Detect architecture
            detector = AppArchitectureDetector()
            result = await detector.detect_with_implications(driver)

            print("✓ Architecture detected!")
            print()
            print(f"Architecture: {result['architecture'].upper()}")
            print(f"Platform: {result['platform']}")
            print(f"Confidence: {result['confidence']:.2f}")
            print()

            print("Evidence:")
            for evidence in result["evidence"]:
                print(f"  • {evidence}")
            print()

            print("Testing Implications:")
            for implication in result["implications"]:
                print(f"  → {implication}")

            driver.quit()

        except Exception as e:
            print(f"❌ Failed to connect to app: {e}")
            print()
            print("💡 To run this demo:")
            print("   1. Install Appium: npm install -g appium")
            print("   2. Start Appium server: appium")
            print("   3. Start Android emulator")
            print("   4. Install your e-commerce app")
            print("   5. Update app_package and app_activity above")

    except ImportError:
        print("❌ Appium not installed - showing simulated demo")
        print()
        await demo_simulated()

    print()
    print("=" * 80)


async def demo_simulated():
    """Demo: Simulated architecture detection results."""
    print("SIMULATED ARCHITECTURE DETECTION")
    print("-" * 80)
    print()

    scenarios = [
        {
            "app": "Nike Android App",
            "architecture": "native",
            "confidence": 0.95,
            "evidence": [
                "Context analysis indicates native (score: 1.00)",
                "DOM accessibility indicates native (score: 0.80)",
                "View hierarchy indicates native (score: 0.80)",
            ],
            "implications": [
                "Test all UX checks - fully native implementation",
                "Performance likely optimal",
                "Platform-specific UI patterns expected",
                "No web version cross-reference needed",
            ],
        },
        {
            "app": "Temu Android App",
            "architecture": "webview",
            "confidence": 0.89,
            "evidence": [
                "Context analysis indicates webview (score: 0.90)",
                "DOM accessibility indicates webview (score: 0.80)",
                "JavaScript execution indicates webview (score: 0.70)",
            ],
            "implications": [
                "Test all UX checks - UI interactions differ from web",
                "Check if issues also exist on mobile web",
                "Touch interactions may differ from web",
                "Performance may be slower than native",
                "Fixing web version may fix app version",
            ],
        },
        {
            "app": "Amazon Android App",
            "architecture": "hybrid",
            "confidence": 0.76,
            "evidence": [
                "Context analysis indicates hybrid (score: 0.90)",
                "DOM accessibility indicates webview (score: 0.80)",
                "View hierarchy indicates hybrid (score: 0.60)",
            ],
            "implications": [
                "Test all UX checks - mixed implementation",
                "Some screens native, some WebView",
                "Test transitions between native and WebView",
                "Performance varies by screen type",
            ],
        },
    ]

    for scenario in scenarios:
        print(f"App: {scenario['app']}")
        print(f"Architecture: {scenario['architecture'].upper()}")
        print(f"Confidence: {scenario['confidence']:.2f}")
        print()

        print("Evidence:")
        for evidence in scenario["evidence"]:
            print(f"  • {evidence}")
        print()

        print("Testing Implications:")
        for implication in scenario["implications"]:
            print(f"  → {implication}")

        print()
        print("-" * 80)
        print()


async def demo_detection_workflow():
    """Demo: Complete detection workflow."""
    print("\n" + "=" * 80)
    print("COMPLETE DETECTION WORKFLOW")
    print("=" * 80)
    print()

    print("Workflow: Discover platforms → Detect architecture → Plan testing")
    print()

    # Step 1: Platform Discovery
    print("Step 1: Platform Discovery")
    print("-" * 80)

    try:
        from ux_journey_scraper.core import discover_platforms

        result = await discover_platforms("Target")

        print(f"✓ Discovered {len(result.platforms_available)} platforms for Target:")
        if "web" in result.platforms_available:
            print(f"   🌐 Web: {result.web_url}")
        if "android" in result.platforms_available:
            print(f"   🤖 Android: {result.android_package}")
        if "ios" in result.platforms_available:
            print(f"   🍎 iOS: {result.ios_bundle_id}")

    except Exception as e:
        print(f"   Error: {e}")

    print()

    # Step 2: Architecture Detection
    print("Step 2: Architecture Detection")
    print("-" * 80)
    print("   (Would connect to Appium and detect architecture)")
    print("   Example result: WebView wrapper (confidence: 0.89)")
    print()

    # Step 3: Testing Strategy
    print("Step 3: Smart Testing Strategy")
    print("-" * 80)
    print("   Based on architecture detection:")
    print("   → Test all 75 UX checks on web")
    print("   → Test all 75 UX checks on Android (WebView)")
    print("   → Test all 75 UX checks on iOS (native)")
    print()
    print("   Failure analysis:")
    print("   → If Android & web both fail → Root cause: shared HTML/CSS")
    print("   → If only Android fails → Root cause: touch interactions")
    print("   → If only iOS fails → Root cause: platform-specific implementation")
    print()

    print("=" * 80)


if __name__ == "__main__":
    print("\n🚀 Starting App Architecture Detection Demos...")
    print()

    # Run demos
    asyncio.run(demo_architecture_detection())
    asyncio.run(demo_detection_workflow())

    print("\n✨ All demos complete!")
    print()
    print("📝 Note: This is a PUBLIC module (no proprietary Baymard data)")
    print("   • Detects app architecture (native/WebView/hybrid)")
    print("   • Provides testing implications")
    print("   • No UX testing logic here")
    print("   • Exports generic JSON for private analysis")
