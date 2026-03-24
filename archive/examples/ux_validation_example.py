#!/usr/bin/env python3
"""
Example: UX Validation during Journey Recording

This example demonstrates how to use the Baymard UX validator
during journey recording to automatically check pages against
UX best practices.
"""
import asyncio
from pathlib import Path

from ux_journey_scraper.core.journey_recorder import JourneyRecorder


async def main():
    """Run journey recording with UX validation."""

    # Path to Baymard guidelines
    # Update this path to your actual guidelines file
    guidelines_path = Path(__file__).parent.parent.parent.parent / "path/to/your/processed_guidelines.json"

    if not guidelines_path.exists():
        print(f"❌ Guidelines file not found at: {guidelines_path}")
        print("\nPlease update the guidelines_path in this script to point to your processed_guidelines.json")
        return

    # Example: Record a journey with UX validation
    recorder = JourneyRecorder(
        start_url="https://www.etsy.com",  # Example e-commerce site
        viewport=(1920, 1080),
        blur_pii=True,
        respect_robots=True,
        headless=False,  # Set to True for headless mode
        output_dir="./journey_with_validation",
        ux_validation_enabled=True,  # Enable UX validation
        guidelines_path=str(guidelines_path),
    )

    print("\n" + "="*60)
    print("UX VALIDATION JOURNEY RECORDING")
    print("="*60)
    print("\nThis will record a journey and validate each page against")
    print("Baymard Institute UX guidelines.\n")

    # Option 1: Interactive recording (navigate manually)
    # journey = await recorder.record()

    # Option 2: Automated recording with specific URLs
    urls = [
        "https://www.etsy.com",
        "https://www.etsy.com/search?q=coffee+mug",
    ]

    journey = await recorder.record_automated(urls)

    # Save journey with validation results
    output_file = "./journey_with_validation/journey_validated.json"
    journey.save(output_file)

    print("\n" + "="*60)
    print("JOURNEY SUMMARY")
    print("="*60)
    print(f"\nTotal steps: {len(journey.steps)}")

    # Print UX validation summary for each step
    for step in journey.steps:
        if step.ux_validation:
            val = step.ux_validation
            print(f"\nStep {step.step_number}: {step.title}")
            print(f"  URL: {step.url}")
            print(f"  Page Type: {val['page_type']}")
            print(f"  Compliance Score: {val['compliance_score']}%")
            print(f"  Guidelines Checked: {val['total_guidelines_checked']}")
            print(f"  Violations: {len(val['violations'])}")
            print(f"  Warnings: {len(val['warnings'])}")
            print(f"  Passed: {len(val['passed'])}")

            if val['violations']:
                print(f"\n  Top Violations:")
                for violation in val['violations'][:3]:
                    print(f"    - #{violation['guideline_id']}: {violation['title']}")
                    print(f"      Severity: {violation['severity']}")
                    print(f"      {violation['details']}")

    print(f"\n✅ Complete journey saved to: {output_file}")
    print("\nYou can now analyze the validation results in the JSON file.")


if __name__ == "__main__":
    asyncio.run(main())
