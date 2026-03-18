"""
Main journey recorder engine using Playwright.
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

from ux_journey_scraper.core.page_analyzer import PageAnalyzer
from ux_journey_scraper.core.robots_checker import RobotsChecker
from ux_journey_scraper.core.screenshot_manager import ScreenshotManager


class JourneyStep:
    """Represents a single step in a user journey."""

    def __init__(self, step_number, url, title, screenshot_path, page_data):
        self.step_number = step_number
        self.url = url
        self.title = title
        self.screenshot_path = screenshot_path
        self.page_data = page_data
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        """Convert step to dictionary."""
        return {
            "step_number": self.step_number,
            "url": self.url,
            "title": self.title,
            "screenshot_path": self.screenshot_path,
            "timestamp": self.timestamp,
            "page_data": self.page_data,
        }


class Journey:
    """Represents a complete user journey."""

    def __init__(self, start_url, viewport=(1920, 1080)):
        self.start_url = start_url
        self.viewport = viewport
        self.steps = []
        self.start_time = datetime.now().isoformat()
        self.end_time = None

    def add_step(self, step):
        """Add a step to the journey."""
        self.steps.append(step)

    def complete(self):
        """Mark journey as complete."""
        self.end_time = datetime.now().isoformat()

    def to_dict(self):
        """Convert journey to dictionary."""
        return {
            "start_url": self.start_url,
            "viewport": {"width": self.viewport[0], "height": self.viewport[1]},
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_steps": len(self.steps),
            "steps": [step.to_dict() for step in self.steps],
        }

    def save(self, filepath):
        """Save journey to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"\n✓ Journey saved to: {filepath}")

    @classmethod
    def load(cls, filepath):
        """Load journey from JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        journey = cls(data["start_url"], (data["viewport"]["width"], data["viewport"]["height"]))
        journey.start_time = data["start_time"]
        journey.end_time = data["end_time"]

        for step_data in data["steps"]:
            step = JourneyStep(
                step_data["step_number"],
                step_data["url"],
                step_data["title"],
                step_data["screenshot_path"],
                step_data["page_data"],
            )
            step.timestamp = step_data["timestamp"]
            journey.steps.append(step)

        return journey


class JourneyRecorder:
    """Record user journeys through websites."""

    def __init__(
        self,
        start_url,
        viewport=(1920, 1080),
        blur_pii=True,
        respect_robots=True,
        headless=False,
        output_dir="journey_output",
    ):
        """
        Initialize journey recorder.

        Args:
            start_url: Starting URL for the journey
            viewport: Viewport size as (width, height)
            blur_pii: Whether to blur PII in screenshots
            respect_robots: Whether to check robots.txt
            headless: Run browser in headless mode
            output_dir: Directory for output files
        """
        self.start_url = start_url
        self.viewport = viewport
        self.blur_pii = blur_pii
        self.respect_robots = respect_robots
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Initialize components
        self.screenshot_manager = ScreenshotManager(
            output_dir=self.output_dir / "screenshots", blur_pii=blur_pii
        )
        self.page_analyzer = PageAnalyzer()
        self.robots_checker = RobotsChecker() if respect_robots else None

        self.journey = None
        self.current_step = 0

    async def record(self):
        """
        Start recording a journey interactively.

        Returns:
            Journey: Recorded journey object
        """
        # Check robots.txt for start URL
        if self.robots_checker:
            can_proceed = self.robots_checker.check_with_confirmation(
                self.start_url, interactive=not self.headless
            )
            if not can_proceed:
                raise ValueError("Cannot proceed: robots.txt disallows and user declined.")

        print(f"\n🎬 Starting journey recording...")
        print(f"📍 Start URL: {self.start_url}")
        print(f"📐 Viewport: {self.viewport[0]}x{self.viewport[1]}")
        print(f"🔒 PII Blur: {'Enabled' if self.blur_pii else 'Disabled'}")
        print(f"🤖 robots.txt: {'Enabled' if self.respect_robots else 'Disabled'}")

        self.journey = Journey(self.start_url, self.viewport)

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": self.viewport[0], "height": self.viewport[1]}
            )
            page = await context.new_page()

            # Go to start URL
            print(f"\n➜ Navigating to start URL...")
            await page.goto(self.start_url)
            await page.wait_for_load_state("networkidle")

            # Record first step
            await self._record_step(page)

            if not self.headless:
                # Interactive mode: wait for user navigation
                print(f"\n📌 Recording Mode Active")
                print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print(f"")
                print(f"  🖱️  Navigate through the website as a user would")
                print(f"  📸 Each page navigation will be automatically recorded")
                print(f"  🛑 Press Ctrl+C to stop recording")
                print(f"")
                print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

                # Listen for navigation events
                previous_url = page.url

                try:
                    while True:
                        await asyncio.sleep(1)  # Check every second

                        current_url = page.url
                        if current_url != previous_url:
                            # New page detected
                            await page.wait_for_load_state("networkidle")
                            await self._record_step(page)
                            previous_url = current_url

                except KeyboardInterrupt:
                    print(f"\n\n🛑 Stopping recording...")

            await browser.close()

        # Complete journey
        self.journey.complete()

        print(f"\n✅ Journey recording complete!")
        print(f"📊 Total steps recorded: {len(self.journey.steps)}")

        return self.journey

    async def _record_step(self, page):
        """Record a single journey step."""
        self.current_step += 1

        print(f"\n📸 Recording Step {self.current_step}...")

        # Capture screenshot
        screenshot_path = await self.screenshot_manager.capture_screenshot(page, self.current_step)
        print(f"   ✓ Screenshot: {screenshot_path}")

        # Analyze page
        page_data = await self.page_analyzer.analyze_page(page)
        print(f"   ✓ Page analyzed: {page.url}")

        # Create step
        step = JourneyStep(
            step_number=self.current_step,
            url=page.url,
            title=await page.title(),
            screenshot_path=screenshot_path,
            page_data=page_data,
        )

        # Add to journey
        self.journey.add_step(step)

        print(f"   ✓ Step {self.current_step} recorded: {step.title}")

    async def record_automated(self, urls):
        """
        Record a journey through a predefined list of URLs.

        Args:
            urls: List of URLs to visit

        Returns:
            Journey: Recorded journey object
        """
        print(f"\n🎬 Starting automated journey recording...")
        print(f"📋 URLs to record: {len(urls)}")

        self.journey = Journey(urls[0], self.viewport)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": self.viewport[0], "height": self.viewport[1]}
            )
            page = await context.new_page()

            for i, url in enumerate(urls, 1):
                # Check robots.txt
                if self.robots_checker:
                    can_proceed = self.robots_checker.check_with_confirmation(
                        url, interactive=False  # Non-interactive for automated
                    )
                    if not can_proceed:
                        print(f"⚠️  Skipping {url} (robots.txt)")
                        continue

                print(f"\n➜ [{i}/{len(urls)}] Navigating to: {url}")

                try:
                    await page.goto(url, timeout=30000)
                    await page.wait_for_load_state("networkidle", timeout=10000)

                    # Record step
                    await self._record_step(page)

                    # Small delay between pages
                    await asyncio.sleep(2)

                except Exception as e:
                    print(f"   ✗ Error loading {url}: {e}")
                    continue

            await browser.close()

        self.journey.complete()

        print(f"\n✅ Automated journey recording complete!")
        print(f"📊 Total steps recorded: {len(self.journey.steps)}")

        return self.journey
