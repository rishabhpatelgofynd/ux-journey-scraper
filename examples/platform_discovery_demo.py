"""
Platform Discovery Demo

Demonstrates automatic discovery of web, Android, and iOS platforms for e-commerce brands.
"""
import asyncio
from ux_journey_scraper.core import PlatformDiscovery, discover_platforms


async def demo_single_brand():
    """Demo: Discover platforms for a single brand."""
    print("=" * 80)
    print("PLATFORM DISCOVERY DEMO - Single Brand")
    print("=" * 80)
    print()

    brand = "Nike"
    print(f"🔍 Discovering platforms for: {brand}")
    print()

    # Method 1: Using convenience function
    result = await discover_platforms(brand)

    print(f"✓ Discovery complete!")
    print()
    print(f"Brand: {result.brand_name}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Platforms available: {', '.join(result.platforms_available)}")
    print()

    if result.web_url:
        print(f"🌐 Web URL: {result.web_url}")
    if result.android_package:
        print(f"🤖 Android Package: {result.android_package}")
    if result.ios_bundle_id:
        print(f"🍎 iOS Bundle ID: {result.ios_bundle_id}")

    print()
    print("=" * 80)


async def demo_multiple_brands():
    """Demo: Discover platforms for multiple brands in parallel."""
    print("\n" + "=" * 80)
    print("PLATFORM DISCOVERY DEMO - Multiple Brands (Parallel)")
    print("=" * 80)
    print()

    brands = ["Amazon", "Target", "Walmart", "Temu", "Wish"]

    print(f"🔍 Discovering platforms for {len(brands)} brands in parallel...")
    print()

    # Method 2: Using PlatformDiscovery class for batch operations
    async with PlatformDiscovery() as discovery:
        results = await discovery.discover_batch(brands)

    # Display results in table format
    print(f"{'Brand':<15} {'Web':<8} {'Android':<8} {'iOS':<8} {'Confidence':<12}")
    print("-" * 80)

    for brand, result in results.items():
        web_status = "✓" if result.web_url else "✗"
        android_status = "✓" if result.android_package else "✗"
        ios_status = "✓" if result.ios_bundle_id else "✗"
        confidence = f"{result.confidence:.2f}"

        print(f"{brand:<15} {web_status:<8} {android_status:<8} {ios_status:<8} {confidence:<12}")

    print()
    print("=" * 80)


async def demo_detailed_results():
    """Demo: Show detailed discovery results."""
    print("\n" + "=" * 80)
    print("PLATFORM DISCOVERY DEMO - Detailed Results")
    print("=" * 80)
    print()

    brand = "Amazon"

    async with PlatformDiscovery() as discovery:
        result = await discovery.discover(brand)

    print(f"Brand: {result.brand_name}")
    print(f"Confidence: {result.confidence:.2f}")
    print()

    print("Platform Details:")
    print("-" * 80)

    if result.web_url:
        print(f"🌐 Web:")
        print(f"   URL: {result.web_url}")
        print(f"   Discovery method: {result.metadata.get('web_discovery_method', 'N/A')}")
        print()

    if result.android_package:
        print(f"🤖 Android:")
        print(f"   Package: {result.android_package}")
        print(f"   Discovery method: {result.metadata.get('android_discovery_method', 'N/A')}")
        print()

    if result.ios_bundle_id:
        print(f"🍎 iOS:")
        print(f"   Bundle ID: {result.ios_bundle_id}")
        print(f"   Discovery method: {result.metadata.get('ios_discovery_method', 'N/A')}")
        print()

    print("=" * 80)


async def demo_usage_scenario():
    """Demo: Realistic usage scenario for testing."""
    print("\n" + "=" * 80)
    print("REALISTIC USAGE SCENARIO")
    print("=" * 80)
    print()

    print("Scenario: You want to test an e-commerce brand across all platforms")
    print()

    brand = "Nike"
    print(f"Step 1: Discover all platforms for '{brand}'")
    print("-" * 80)

    result = await discover_platforms(brand)

    print(f"✓ Found {len(result.platforms_available)} platforms: {', '.join(result.platforms_available)}")
    print()

    print("Step 2: Plan testing strategy")
    print("-" * 80)

    if 'web' in result.platforms_available:
        print(f"✓ Web testing: Test at {result.web_url}")

    if 'android' in result.platforms_available:
        print(f"✓ Android testing: Test package {result.android_package}")

    if 'ios' in result.platforms_available:
        print(f"✓ iOS testing: Test bundle {result.ios_bundle_id}")

    print()
    print("Step 3: Run UX checks on all platforms")
    print("-" * 80)
    print("(This would be done by the private baymaar-guidelines package)")
    print()

    print("💡 Next steps:")
    print("   1. Export this data to JSON")
    print("   2. Import in baymaar-guidelines")
    print("   3. Run 75+ UX checks on all platforms")
    print("   4. Cross-reference failures across platforms")

    print()
    print("=" * 80)


if __name__ == "__main__":
    print("\n🚀 Starting Platform Discovery Demos...")
    print()

    # Run all demos
    asyncio.run(demo_single_brand())
    asyncio.run(demo_multiple_brands())
    asyncio.run(demo_detailed_results())
    asyncio.run(demo_usage_scenario())

    print("\n✨ All demos complete!")
    print()
    print("📝 Note: This is a PUBLIC module (no proprietary Baymard data)")
    print("   • Discovers platforms automatically")
    print("   • No UX testing logic here")
    print("   • Exports generic JSON for private analysis")
