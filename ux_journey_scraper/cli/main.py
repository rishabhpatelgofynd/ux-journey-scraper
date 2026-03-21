"""
Command-line interface for UX Journey Scraper.
"""
import asyncio
from pathlib import Path

import click

from ux_journey_scraper.config.scrape_config import ScrapeConfig
from ux_journey_scraper.core.autonomous_crawler import AutonomousCrawler
from ux_journey_scraper.core.journey_recorder import Journey, JourneyRecorder

try:
    from ux_journey_scraper.core.appium_crawler import AppiumCrawler
    _APPIUM_AVAILABLE = True
except ImportError:
    _APPIUM_AVAILABLE = False


@click.group()
@click.version_option(version="0.5.0")
def cli():
    """UX Journey Scraper - Autonomous web crawler for capturing user journeys."""
    pass


@cli.command()
@click.option("--config", required=True, help="Path to YAML configuration file")
@click.option("--output-dir", default="journey_output", help="Output directory for results")
def crawl(config, output_dir):
    """Autonomous crawl using YAML configuration (v0.5.0)."""
    click.echo(f"\n{'='*60}")
    click.echo(f"  UX JOURNEY AUTONOMOUS CRAWLER v0.5.0")
    click.echo(f"{'='*60}\n")

    try:
        # Load configuration
        click.echo(f"Loading configuration from: {config}")
        scrape_config = ScrapeConfig.load(config)
        click.echo(f"Configuration loaded")
        click.echo(f"   Target: {scrape_config.target['name']}")
        click.echo(f"   Base URL: {scrape_config.target['base_url']}")
        click.echo(f"   Platforms: {len(scrape_config.platforms)}")
        click.echo(f"   Seed URLs: {len(scrape_config.seed_urls)}")
        click.echo(f"   Max pages: {scrape_config.crawler.max_pages}")

        # Run crawl for each platform
        click.echo(f"\nStarting multi-platform crawl...\n")
        total_pages = 0
        for platform in scrape_config.platforms:
            platform_dir = Path(output_dir) / platform.type

            if platform.is_native:
                # ---- Native app crawl via Appium ----
                if not _APPIUM_AVAILABLE:
                    click.echo(f"  Skipping {platform.type}: Appium not installed.")
                    click.echo("    Install: pip install 'ux-journey-scraper[native]'")
                    click.echo("    Then run: appium driver install uiautomator2 xcuitest")
                    continue
                click.echo(f"Platform: {platform.type} (native app via Appium)")
                crawler = AppiumCrawler(
                    config=scrape_config,
                    output_dir=str(platform_dir),
                    platform=platform,
                )
            else:
                # ---- Web crawl via Playwright ----
                viewport = platform.viewport or {}
                w = viewport.get("width", "?")
                h = viewport.get("height", "?")
                click.echo(f"Platform: {platform.type} ({w}x{h})")
                crawler = AutonomousCrawler(
                    config=scrape_config,
                    output_dir=str(platform_dir),
                    platform=platform,
                )

            journey = asyncio.run(crawler.crawl())

            output_file = platform_dir / "journey.json"
            journey.save(str(output_file))

            stats = crawler.get_stats()
            pages = stats['pages_captured']
            total_pages += pages
            click.echo(f"  {platform.type}: {pages} pages -> {output_file}")

        click.echo(f"\n{'='*60}")
        click.echo(f"All platforms complete!")
        click.echo(f"Total pages captured: {total_pages}")
        click.echo(f"Output directory: {output_dir}")
        click.echo(f"{'='*60}\n")

    except FileNotFoundError as e:
        click.echo(f"\nConfiguration file not found: {e}")
    except Exception as e:
        click.echo(f"\nCrawl error: {e}")
        import traceback
        traceback.print_exc()


@cli.command()
@click.option("--start-url", required=True, help="Starting URL for the journey")
@click.option("--output", default="journey.json", help="Output file path")
@click.option("--viewport", default="1920x1080", help="Viewport size (e.g., 1920x1080)")
@click.option("--blur-pii/--no-blur-pii", default=True, help="Blur PII in screenshots")
@click.option("--respect-robots/--ignore-robots", default=True, help="Respect robots.txt")
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode")
def record(start_url, output, viewport, blur_pii, respect_robots, headless):
    """[DEPRECATED] Record a user journey interactively. Use 'crawl' for v0.2.0 features."""
    click.echo("⚠️  WARNING: This command is deprecated. Use 'ux-journey crawl --config <file>' for v0.2.0 features.\n")
    try:
        # Parse viewport
        width, height = map(int, viewport.split("x"))
    except ValueError:
        click.echo("❌ Invalid viewport format. Use WIDTHxHEIGHT (e.g., 1920x1080)")
        return

    click.echo(f"\n{'='*60}")
    click.echo(f"  UX JOURNEY RECORDER")
    click.echo(f"{'='*60}\n")

    # Create recorder
    recorder = JourneyRecorder(
        start_url=start_url,
        viewport=(width, height),
        blur_pii=blur_pii,
        respect_robots=respect_robots,
        headless=headless,
    )

    # Record journey
    try:
        journey = asyncio.run(recorder.record())

        # Save journey
        journey.save(output)

        click.echo(f"\n{'='*60}")
        click.echo(f"✅ Journey recording complete!")
        click.echo(f"📁 Saved to: {output}")
        click.echo(f"{'='*60}\n")

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Recording cancelled by user")
    except Exception as e:
        click.echo(f"\n❌ Error during recording: {e}")


@cli.command()
@click.argument("journey_file", type=click.Path(exists=True))
def info(journey_file):
    """Show information about a recorded journey."""
    try:
        journey = Journey.load(journey_file)

        click.echo(f"\n{'='*60}")
        click.echo(f"  JOURNEY INFO")
        click.echo(f"{'='*60}\n")
        click.echo(f"📍 Start URL: {journey.start_url}")
        click.echo(f"📐 Viewport: {journey.viewport[0]}x{journey.viewport[1]}")
        click.echo(f"⏱️  Start Time: {journey.start_time}")
        click.echo(f"⏱️  End Time: {journey.end_time}")
        click.echo(f"📊 Total Steps: {len(journey.steps)}")
        click.echo(f"\nSteps:")
        for step in journey.steps:
            click.echo(f"  {step.step_number}. {step.title} ({step.url})")
        click.echo(f"\n{'='*60}\n")

    except Exception as e:
        click.echo(f"❌ Error loading journey: {e}")


if __name__ == "__main__":
    cli()
