"""Tests for WebKit engine integration."""
import pytest


def test_crawlee_adapter_uses_webkit_by_default():
    from ux_journey_scraper.core.crawlee_adapter import CrawleeAdapter
    from ux_journey_scraper.config.scrape_config import (
        ScrapeConfig, PlatformConfig, AuthConfig,
    )
    config = ScrapeConfig(
        target={"name": "Test", "base_url": "https://example.com"},
        platforms=[PlatformConfig(type="web_desktop", viewport={"width": 1920, "height": 1080})],
        auth=AuthConfig(logged_out=True, logged_in=False),
        seed_urls=["https://example.com"],
    )
    adapter = CrawleeAdapter(config=config, output_dir="/tmp/test-webkit")
    assert adapter.browser_type == "webkit"


def test_crawlee_adapter_chromium_override():
    from ux_journey_scraper.core.crawlee_adapter import CrawleeAdapter
    from ux_journey_scraper.config.scrape_config import (
        ScrapeConfig, PlatformConfig, AuthConfig,
    )
    config = ScrapeConfig(
        target={"name": "Test", "base_url": "https://example.com"},
        platforms=[PlatformConfig(type="web_desktop", viewport={"width": 1920, "height": 1080})],
        auth=AuthConfig(logged_out=True, logged_in=False),
        seed_urls=["https://example.com"],
    )
    adapter = CrawleeAdapter(config=config, output_dir="/tmp/test-chromium", browser_type="chromium")
    assert adapter.browser_type == "chromium"
