#!/usr/bin/env python3
"""
Example: Comprehensive UX Testing with Journey Recording

This example demonstrates integration with the full BayMAAR UX Testing System
which includes:
- 569 guidelines with test criteria
- Automated Playwright checks
- Impact-weighted scoring from benchmark data
- Priority recommendations

This is the COMPLETE testing system, not just simple validation.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

# Import the comprehensive validator
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ux_journey_scraper.validators import ComprehensiveUXValidator, COMPREHENSIVE_VALIDATOR_AVAILABLE


async def test_single_page():
    """Test a single page with comprehensive UX validation."""

    if not COMPREHENSIVE_VALIDATOR_AVAILABLE:
        print("❌ Comprehensive UX validator not available")
        print("   Ensure research/baymaar-guidelines is accessible")
        return

    print("\n" + "="*70)
    print("COMPREHENSIVE UX TESTING DEMO")
    print("="*70)

    # Initialize validator
    print("\n📋 Initializing UX testing system...")
    validator = ComprehensiveUXValidator(
        enable_vision_checks=False,  # Set to True for vision-based testing
        enable_scoring=True  # Enable impact-weighted scoring
    )

    # Show coverage stats
    stats = validator.get_coverage_stats()
    print(f"\n✓ Test System Ready:")
    print(f"  - {stats['total_checks_registered']} checks registered")
    print(f"  - {stats['automated_checks']} automated checks")
    print(f"  - {stats['guidelines_covered']}/{stats['total_guidelines']} guidelines covered")
    print(f"  - {stats['coverage_percentage']}% coverage")

    # Launch browser and test a page
    async with async_playwright() as p:
        print("\n🌐 Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Test URL
        test_url = "https://www.etsy.com"  # Example e-commerce site
        print(f"\n🔍 Testing: {test_url}")

        try:
            await page.goto(test_url, timeout=30000)
            await page.wait_for_load_state("networkidle")

            print("   ✓ Page loaded")

            # Run comprehensive validation
            print("\n⚙️  Running UX validation...")
            result = await validator.validate_page(
                page,
                test_url,
                page_type="homepage"
            )

            # Generate and display report
            print("\n" + validator.generate_summary_report(result))

            # Show detailed failed checks
            if result['automated_checks']['failed'] > 0:
                print("\n📋 Failed Checks Detail:")
                for check in result['raw_check_results']:
                    if check['status'] == 'failed':
                        print(f"\n  Guideline #{check['guideline_id']} - {check['check_id']}")
                        print(f"  Evidence: {check['evidence']}")

            # Show top priority fixes
            if result['priority_fixes']:
                print("\n🎯 Priority Recommendations:")
                for i, fix in enumerate(result['priority_fixes'][:5], 1):
                    print(f"\n  {i}. Guideline #{fix['guideline_id']}: {fix['title']}")
                    print(f"     Impact: {fix['impact']:+.1f} points")
                    print(f"     Status: {fix['status']}")

        except Exception as e:
            print(f"\n❌ Error: {e}")

        finally:
            await browser.close()

    print("\n✅ Test complete!\n")


async def test_multi_page_journey():
    """Test multiple pages in a journey."""

    if not COMPREHENSIVE_VALIDATOR_AVAILABLE:
        print("❌ Comprehensive UX validator not available")
        return

    print("\n" + "="*70)
    print("MULTI-PAGE JOURNEY TESTING")
    print("="*70)

    validator = ComprehensiveUXValidator(enable_scoring=True)

    test_urls = [
        {"url": "https://www.etsy.com", "type": "homepage"},
        {"url": "https://www.etsy.com/search?q=coffee", "type": "search"},
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        journey_results = []

        for test_data in test_urls:
            url = test_data["url"]
            page_type = test_data["type"]

            print(f"\n🔍 Testing: {url} ({page_type})")

            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle")

                result = await validator.validate_page(page, url, page_type)
                journey_results.append(result)

                # Quick summary
                checks = result['automated_checks']
                score = result.get('ux_score', {})
                print(f"   ✓ {checks['passed']} passed, {checks['failed']} failed")
                if score:
                    print(f"   ✓ Score: {score['score']:.1f}/100 ({score['grade']})")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        await browser.close()

        # Journey summary
        print("\n" + "="*70)
        print("JOURNEY SUMMARY")
        print("="*70)

        total_checks = sum(r['automated_checks']['total_checks'] for r in journey_results)
        total_passed = sum(r['automated_checks']['passed'] for r in journey_results)
        total_failed = sum(r['automated_checks']['failed'] for r in journey_results)
        avg_score = sum(r['ux_score']['score'] for r in journey_results if r.get('ux_score')) / len(journey_results)

        print(f"\nPages tested: {len(journey_results)}")
        print(f"Total checks run: {total_checks}")
        print(f"Overall pass rate: {(total_passed/total_checks*100):.1f}%")
        print(f"Average UX score: {avg_score:.1f}/100")

        # Collect all unique violations
        all_violations = set()
        for result in journey_results:
            for check in result['raw_check_results']:
                if check['status'] == 'failed':
                    all_violations.add(check['guideline_id'])

        print(f"\nUnique guidelines violated: {len(all_violations)}")
        print("Guideline IDs:", ", ".join(sorted(all_violations)))

    print("\n✅ Journey test complete!\n")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  BayMAAR Comprehensive UX Testing System                    ║
    ║                                                              ║
    ║  Features:                                                   ║
    ║  • 569 guidelines with test criteria                        ║
    ║  • Automated Playwright-based checks                        ║
    ║  • Impact-weighted scoring from benchmark data              ║
    ║  • Priority recommendations                                  ║
    ║  • Vision-based testing (optional)                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    print("Choose a demo:")
    print("1. Test single page")
    print("2. Test multi-page journey")
    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        asyncio.run(test_single_page())
    elif choice == "2":
        asyncio.run(test_multi_page_journey())
    else:
        print("Invalid choice")
