"""
Command-line interface for UX Journey Scraper.
"""
import asyncio
from pathlib import Path

import click

from ux_journey_scraper.analyzers.journey_flow import JourneyFlowAnalyzer
from ux_journey_scraper.analyzers.ux_analyzer import UXAnalyzer
from ux_journey_scraper.core.journey_recorder import Journey, JourneyRecorder
from ux_journey_scraper.reporters.html_reporter import HTMLReporter
from ux_journey_scraper.reporters.json_reporter import JSONReporter


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """UX Journey Scraper - Record and analyze user journeys with UX guidelines."""
    pass


@cli.command()
@click.option("--start-url", required=True, help="Starting URL for the journey")
@click.option("--output", default="journey.json", help="Output file path")
@click.option("--viewport", default="1920x1080", help="Viewport size (e.g., 1920x1080)")
@click.option("--blur-pii/--no-blur-pii", default=True, help="Blur PII in screenshots")
@click.option("--respect-robots/--ignore-robots", default=True, help="Respect robots.txt")
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode")
def record(start_url, output, viewport, blur_pii, respect_robots, headless):
    """Record a user journey interactively."""
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
@click.option("--output-dir", default="./reports", help="Output directory for reports")
@click.option(
    "--format", type=click.Choice(["html", "json", "both"]), default="both", help="Report format"
)
@click.option(
    "--guidelines",
    type=click.Choice(["all", "essential", "high"]),
    default="all",
    help="Guideline priority",
)
def analyze(journey_file, output_dir, format, guidelines):
    """Analyze a recorded journey against UX guidelines."""
    click.echo(f"\n{'='*60}")
    click.echo(f"  UX JOURNEY ANALYZER")
    click.echo(f"{'='*60}\n")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    # Load journey
    click.echo(f"📂 Loading journey from: {journey_file}")
    journey = Journey.load(journey_file)
    click.echo(f"✓ Journey loaded: {len(journey.steps)} steps\n")

    # Analyze UX
    analyzer = UXAnalyzer(guideline_priority=guidelines)
    analysis = analyzer.analyze(journey)

    # Analyze flow
    flow_analyzer = JourneyFlowAnalyzer()
    flow_analysis = flow_analyzer.analyze_flow(journey)

    click.echo(f"\n{'='*60}")
    click.echo(f"  GENERATING REPORTS")
    click.echo(f"{'='*60}\n")

    # Generate reports
    json_reporter = JSONReporter()
    html_reporter = HTMLReporter()

    if format in ["json", "both"]:
        json_path = output_path / "journey-analysis.json"
        json_reporter.generate_report(analysis, json_path)

        flow_json_path = output_path / "journey-flow.json"
        json_reporter.generate_flow_report(flow_analysis, flow_json_path)

    if format in ["html", "both"]:
        html_path = output_path / "journey-report.html"
        html_reporter.generate_report(analysis, journey, html_path, include_screenshots=True)

    click.echo(f"\n{'='*60}")
    click.echo(f"✅ Analysis complete!")
    click.echo(f"📊 Overall Score: {analysis.overall_score}/100")
    click.echo(
        f"⚠️  Total Issues: {analysis.total_violations + analysis.total_accessibility_issues}"
    )
    click.echo(f"📁 Reports saved to: {output_dir}")
    click.echo(f"{'='*60}\n")


@cli.command()
@click.option("--start-url", required=True, help="Starting URL for the journey")
@click.option("--output", default="journey", help="Output file prefix")
@click.option("--viewport", default="1920x1080", help="Viewport size")
@click.option("--blur-pii/--no-blur-pii", default=True, help="Blur PII in screenshots")
@click.option("--respect-robots/--ignore-robots", default=True, help="Respect robots.txt")
@click.option("--analyze/--no-analyze", default=True, help="Run analysis after recording")
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode")
def run(start_url, output, viewport, blur_pii, respect_robots, analyze_flag, headless):
    """Record and analyze a journey in one command."""
    try:
        # Parse viewport
        width, height = map(int, viewport.split("x"))
    except ValueError:
        click.echo("❌ Invalid viewport format. Use WIDTHxHEIGHT (e.g., 1920x1080)")
        return

    click.echo(f"\n{'='*60}")
    click.echo(f"  UX JOURNEY SCRAPER")
    click.echo(f"{'='*60}\n")

    # Record journey
    journey_file = f"{output}.json"
    recorder = JourneyRecorder(
        start_url=start_url,
        viewport=(width, height),
        blur_pii=blur_pii,
        respect_robots=respect_robots,
        headless=headless,
    )

    try:
        journey = asyncio.run(recorder.record())
        journey.save(journey_file)

        # Analyze if requested
        if analyze_flag:
            # Create output directory
            output_dir = f"{output}_reports"
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True, parents=True)

            # Analyze
            analyzer = UXAnalyzer()
            analysis = analyzer.analyze(journey)

            # Generate reports
            json_reporter = JSONReporter()
            html_reporter = HTMLReporter()

            json_reporter.generate_report(analysis, output_path / "analysis.json")
            html_reporter.generate_report(analysis, journey, output_path / "report.html")

            click.echo(f"\n{'='*60}")
            click.echo(f"✅ Complete!")
            click.echo(f"📁 Journey: {journey_file}")
            click.echo(f"📊 Reports: {output_dir}")
            click.echo(f"🎯 Score: {analysis.overall_score}/100")
            click.echo(f"{'='*60}\n")
        else:
            click.echo(f"\n{'='*60}")
            click.echo(f"✅ Recording complete!")
            click.echo(f"📁 Journey: {journey_file}")
            click.echo(f"{'='*60}\n")

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Cancelled by user")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")


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
