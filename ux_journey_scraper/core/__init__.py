"""Core modules for journey recording."""

from ux_journey_scraper.core.journey_recorder import Journey, JourneyRecorder, JourneyStep
from ux_journey_scraper.core.page_analyzer import PageAnalyzer
from ux_journey_scraper.core.robots_checker import RobotsChecker
from ux_journey_scraper.core.screenshot_manager import ScreenshotManager
from ux_journey_scraper.core.platform_discovery import (
    PlatformDiscovery,
    PlatformDiscoveryResult,
    discover_platforms,
)
from ux_journey_scraper.core.app_architecture_detector import (
    AppArchitectureDetector,
    ArchitectureDetectionResult,
    detect_architecture,
)

__all__ = [
    "JourneyRecorder",
    "Journey",
    "JourneyStep",
    "ScreenshotManager",
    "PageAnalyzer",
    "RobotsChecker",
    "PlatformDiscovery",
    "PlatformDiscoveryResult",
    "discover_platforms",
    "AppArchitectureDetector",
    "ArchitectureDetectionResult",
    "detect_architecture",
]
