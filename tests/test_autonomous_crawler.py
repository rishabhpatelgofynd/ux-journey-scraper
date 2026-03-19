"""
Tests for autonomous crawler functionality.
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from ux_journey_scraper.config.scrape_config import (
    ScrapeConfig,
    PlatformConfig,
    AuthConfig,
    FormFillConfig,
    CrawlerConfig,
)
from ux_journey_scraper.core.navigation_queue import NavigationAction, NavigationQueue
from ux_journey_scraper.core.state_registry import StateRegistry
from ux_journey_scraper.core.element_intelligence import ElementIntelligence


class TestScrapeConfig:
    """Test YAML configuration loading and validation."""

    def test_config_creation(self):
        """Test creating config programmatically."""
        config = ScrapeConfig(
            target={"name": "Test Site", "base_url": "https://example.com"},
            platforms=[
                PlatformConfig(
                    type="web_desktop",
                    viewport={"width": 1920, "height": 1080},
                )
            ],
            auth=AuthConfig(logged_out=True, logged_in=False),
            seed_urls=["https://example.com"],
            form_fill=FormFillConfig(),
            crawler=CrawlerConfig(),
        )

        assert config.target["name"] == "Test Site"
        assert len(config.platforms) == 1
        assert config.platforms[0].type == "web_desktop"
        assert config.seed_urls == ["https://example.com"]

    def test_platform_validation(self):
        """Test platform configuration validation."""
        # Valid platform
        platform = PlatformConfig(
            type="web_desktop",
            viewport={"width": 1920, "height": 1080},
        )
        assert platform.type == "web_desktop"

        # Invalid platform type
        with pytest.raises(ValueError, match="Invalid platform type"):
            PlatformConfig(
                type="invalid_type",
                viewport={"width": 1920, "height": 1080},
            )

        # Invalid viewport
        with pytest.raises(ValueError, match="Viewport must contain"):
            PlatformConfig(
                type="web_desktop",
                viewport={"width": 1920},  # Missing height
            )

    def test_auth_validation(self):
        """Test authentication configuration validation."""
        # Valid logged-out config
        auth = AuthConfig(logged_out=True, logged_in=False)
        assert auth.logged_out is True

        # Invalid logged-in config (missing credentials)
        with pytest.raises(ValueError, match="logged_in=true requires"):
            AuthConfig(
                logged_out=False,
                logged_in=True,
                login_success_indicator="/dashboard",
            )

    def test_form_fill_validation(self):
        """Test form fill configuration validation."""
        # Valid test card
        form_fill = FormFillConfig(card_number="4111111111111111")
        assert form_fill.card_number == "4111111111111111"

        # Invalid real card
        with pytest.raises(ValueError, match="Only test cards allowed"):
            FormFillConfig(card_number="4242424242424242")

    def test_crawler_validation(self):
        """Test crawler configuration validation."""
        # Valid config
        crawler = CrawlerConfig(max_depth=5, max_pages=100)
        assert crawler.max_depth == 5

        # Invalid max_depth
        with pytest.raises(ValueError, match="max_depth must be at least 1"):
            CrawlerConfig(max_depth=0)

        # Invalid timeout
        with pytest.raises(ValueError, match="timeout_per_page_ms must be at least"):
            CrawlerConfig(timeout_per_page_ms=500)

    def test_yaml_loading(self, tmp_path):
        """Test loading configuration from YAML file."""
        # Create test YAML config
        config_file = tmp_path / "test-config.yaml"
        config_file.write_text(
            """
target:
  name: "Test Site"
  base_url: "https://example.com"

platforms:
  - type: web_desktop
    viewport:
      width: 1920
      height: 1080

auth:
  logged_out: true
  logged_in: false

seed_urls:
  - "https://example.com"

crawler:
  max_depth: 5
  max_pages: 50
"""
        )

        # Load config
        config = ScrapeConfig.load(str(config_file))

        assert config.target["name"] == "Test Site"
        assert config.crawler.max_depth == 5
        assert config.crawler.max_pages == 50

    def test_yaml_save(self, tmp_path):
        """Test saving configuration to YAML file."""
        config = ScrapeConfig(
            target={"name": "Test Site", "base_url": "https://example.com"},
            platforms=[
                PlatformConfig(
                    type="web_desktop",
                    viewport={"width": 1920, "height": 1080},
                )
            ],
            auth=AuthConfig(logged_out=True, logged_in=False),
            seed_urls=["https://example.com"],
        )

        # Save config
        config_file = tmp_path / "saved-config.yaml"
        config.save(str(config_file))

        # Load it back
        loaded_config = ScrapeConfig.load(str(config_file))

        assert loaded_config.target["name"] == "Test Site"
        assert loaded_config.platforms[0].viewport["width"] == 1920


class TestNavigationQueue:
    """Test navigation queue priority logic."""

    def test_priority_ordering(self):
        """Test that high-priority actions are processed first."""
        queue = NavigationQueue(max_depth=10)

        # Add actions with different priorities
        queue.add(
            NavigationAction(
                type="click",
                priority=10,
                depth=1,
                url="https://example.com",
                selector="#low-priority",
            )
        )

        queue.add(
            NavigationAction(
                type="click",
                priority=100,
                depth=1,
                url="https://example.com",
                selector="#high-priority",
            )
        )

        queue.add(
            NavigationAction(
                type="click",
                priority=50,
                depth=1,
                url="https://example.com",
                selector="#medium-priority",
            )
        )

        # Should get high-priority first
        action = queue.next()
        assert action.selector == "#high-priority"
        assert action.priority == 100

        # Then medium
        action = queue.next()
        assert action.selector == "#medium-priority"

        # Then low
        action = queue.next()
        assert action.selector == "#low-priority"

    def test_depth_limit(self):
        """Test that actions beyond max_depth are rejected."""
        queue = NavigationQueue(max_depth=3)

        # Add action within depth limit
        added = queue.add(
            NavigationAction(
                type="click",
                priority=50,
                depth=2,
                url="https://example.com",
                selector="#ok",
            )
        )
        assert added is True

        # Add action at exact limit
        added = queue.add(
            NavigationAction(
                type="click",
                priority=50,
                depth=3,
                url="https://example.com",
                selector="#at-limit",
            )
        )
        assert added is True

        # Add action beyond limit
        added = queue.add(
            NavigationAction(
                type="click",
                priority=50,
                depth=4,
                url="https://example.com",
                selector="#too-deep",
            )
        )
        assert added is False


class TestStateRegistry:
    """Test state deduplication logic."""

    def test_url_deduplication(self):
        """Test that identical URLs are detected as duplicates."""
        registry = StateRegistry()

        url = "https://example.com/page"
        dom = "<html><body><h1>Test</h1></body></html>"

        # First visit should be new
        assert registry.is_new_state(url, dom) is True

        # Second visit should be duplicate
        assert registry.is_new_state(url, dom) is False

    def test_url_normalization(self):
        """Test that tracking parameters are normalized."""
        registry = StateRegistry()

        dom = "<html><body>Test</body></html>"

        # Visit URL with tracking params
        assert registry.is_new_state(
            "https://example.com/page?utm_source=test&utm_medium=email", dom
        ) is True

        # Same URL with different tracking params should be duplicate
        assert registry.is_new_state(
            "https://example.com/page?utm_source=other&fbclid=123", dom
        ) is False

        # Same URL without tracking params should also be duplicate
        assert registry.is_new_state("https://example.com/page", dom) is False

    def test_dom_hash_deduplication(self):
        """Test that identical DOM content is detected."""
        registry = StateRegistry()

        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        dom = "<html><body><h1>Same Content</h1></body></html>"

        # First URL with this DOM
        assert registry.is_new_state(url1, dom) is True

        # Different URL with SAME DOM should still be duplicate
        # (This prevents infinite loops on SPAs)
        assert registry.is_new_state(url2, dom) is False

    def test_get_stats(self):
        """Test statistics collection."""
        registry = StateRegistry()

        # First unique state
        dom1 = "<html><body><h1>Page 1</h1><p>Content 1</p></body></html>"
        is_new = registry.is_new_state("https://example.com/page1", dom1)
        assert is_new is True

        # Second unique state (different URL and structurally different DOM)
        dom2 = "<html><body><h1>Page 2</h1><div><p>Content 2</p></div></body></html>"
        is_new = registry.is_new_state("https://example.com/page2", dom2)
        assert is_new is True

        # Duplicate (same URL and DOM)
        is_new = registry.is_new_state("https://example.com/page1", dom1)
        assert is_new is False

        stats = registry.get_stats()
        assert stats["unique_urls"] >= 2
        assert stats["unique_dom_hashes"] >= 2


class TestElementIntelligence:
    """Test element detection and priority scoring."""

    def test_priority_scoring(self):
        """Test that CTAs are scored correctly."""
        intelligence = ElementIntelligence()

        # High-priority CTA
        high_priority = intelligence.calculate_priority({"text": "Add to Cart"})
        assert high_priority >= 90

        # Medium-priority CTA
        medium_priority = intelligence.calculate_priority({"text": "Learn More"})
        assert medium_priority < high_priority

        # Low-priority element
        low_priority = intelligence.calculate_priority({"text": "About Us"})
        assert low_priority < medium_priority


@pytest.mark.skip(reason="Requires browser and network access")
class TestIntegration:
    """Integration tests requiring full browser setup."""

    async def test_simple_crawl(self, tmp_path):
        """Test autonomous crawl on a simple site."""
        from ux_journey_scraper.core.autonomous_crawler import AutonomousCrawler

        config = ScrapeConfig(
            target={"name": "Example", "base_url": "https://example.com"},
            platforms=[
                PlatformConfig(
                    type="web_desktop",
                    viewport={"width": 1920, "height": 1080},
                )
            ],
            auth=AuthConfig(logged_out=True, logged_in=False),
            seed_urls=["https://example.com"],
            crawler=CrawlerConfig(max_depth=2, max_pages=3),
        )

        crawler = AutonomousCrawler(config=config, output_dir=str(tmp_path))

        journey = await crawler.crawl()

        assert journey is not None
        assert len(journey.steps) > 0
        assert journey.steps[0].url == "https://example.com"
