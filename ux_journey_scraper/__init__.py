"""
UX Journey Scraper - Autonomous web crawler for capturing user journeys.
"""

__version__ = "0.3.0"

from ux_journey_scraper.config.scrape_config import ScrapeConfig
from ux_journey_scraper.core.autonomous_crawler import AutonomousCrawler
from ux_journey_scraper.core.journey_recorder import JourneyRecorder
from ux_journey_scraper.journey_loader import JourneyLoader, JourneyStep

__all__ = [
    "JourneyRecorder",
    "AutonomousCrawler",
    "ScrapeConfig",
    "JourneyLoader",
    "JourneyStep",
]
