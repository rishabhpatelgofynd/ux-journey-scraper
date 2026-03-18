"""
UX Journey Scraper - Record and analyze user journeys with UX guidelines validation.
"""

__version__ = "0.1.0"

from ux_journey_scraper.analyzers.ux_analyzer import UXAnalyzer
from ux_journey_scraper.core.journey_recorder import JourneyRecorder

__all__ = [
    "JourneyRecorder",
    "UXAnalyzer",
]
