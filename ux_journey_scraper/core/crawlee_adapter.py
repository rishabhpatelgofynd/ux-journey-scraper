"""
Crawlee-powered crawl engine.

Replaces the custom AutonomousCrawler with crawlee-python's PlaywrightCrawler
for battle-tested crawling (fingerprints, request queue, retries, link discovery).

Our analysis layer (screenshots, page analysis, compliance data, form filling,
journey recording) runs on top of crawlee's page loading.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from ux_journey_scraper.config.scrape_config import PlatformConfig, ScrapeConfig
from ux_journey_scraper.core.compliance_data_collector import ComplianceDataCollector
from ux_journey_scraper.core.form_filler import FormFiller
from ux_journey_scraper.core.journey_recorder import Journey, JourneyStep
from ux_journey_scraper.core.page_analyzer import PageAnalyzer
from ux_journey_scraper.core.screenshot_manager import ScreenshotManager
from ux_journey_scraper.core.sitemap_parser import SitemapParser

from ux_journey_scraper.core.design_data_collector import DesignDataCollector
from ux_journey_scraper.core.page_classifier import PageClassifier
from ux_journey_scraper.core.anti_crawler_detector import AntiCrawlerDetector
from ux_journey_scraper.core.page_selector import PageSelector

try:
    from ux_journey_scraper.core.cdp_element_detector import CDPElementDetector

    _CDP_AVAILABLE = True
except ImportError:
    _CDP_AVAILABLE = False

try:
    from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

    _CRAWLEE_AVAILABLE = True
except ImportError:
    _CRAWLEE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Block page signatures
BLOCK_SIGNATURES = [
    "access denied",
    "access is temporarily restricted",
    "403 error",
    "403 forbidden",
    "request blocked",
    "captcha",
    "robot",
    "unusual activity",
    "verify you are human",
    "just a moment",
    "security measure",
]


def is_crawlee_available() -> bool:
    """Check if crawlee is installed."""
    return _CRAWLEE_AVAILABLE


class CrawleeAdapter:
    """Bridges crawlee's PlaywrightCrawler to our journey capture pipeline.

    Crawlee handles: request queue, fingerprints, retries, link discovery, anti-bot.
    Our layer handles: screenshots, page analysis, journey JSON, compliance data.
    """

    def __init__(
        self,
        config: ScrapeConfig,
        output_dir: str = "journey_output",
        platform: Optional[PlatformConfig] = None,
        browser_type: str = "webkit",
    ):
        if not _CRAWLEE_AVAILABLE:
            raise ImportError(
                "crawlee is not installed. Install with: pip install 'crawlee[playwright]'"
            )

        self.browser_type = browser_type
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        self.platform = platform or config.platforms[0]
        self.base_domain = urlparse(config.base_url).netloc.replace("www.", "")

        # Our analysis components
        self.screenshot_manager = ScreenshotManager(
            output_dir=self.output_dir / "screenshots",
            blur_pii=True,
        )
        self.page_analyzer = PageAnalyzer()
        self.compliance_collector = ComplianceDataCollector()
        self.form_filler = FormFiller(config.form_fill)
        self.cdp_detector = CDPElementDetector() if _CDP_AVAILABLE else None
        self.design_collector = DesignDataCollector()

        # Journey state
        self.journey = Journey(
            start_url=config.base_url,
            viewport=(
                self.platform.viewport.get("width", 1920),
                self.platform.viewport.get("height", 1080),
            ),
            platform_type=self.platform.type,
            user_agent=self.platform.user_agent,
        )
        self.pages_captured = 0
        self.captured_urls = set()

    def _is_block_page(self, title: str, text_preview: str) -> bool:
        """Check if the current page is a block/CAPTCHA page."""
        combined = (title + " " + text_preview).lower()
        return any(sig in combined for sig in BLOCK_SIGNATURES)

    async def crawl(self) -> Journey:
        """Run a full-site crawl using crawlee's PlaywrightCrawler.

        Discovery strategy:
        1. Parse sitemap.xml for all known URLs (instant bulk discovery)
        2. Crawl each page and extract links (catches pages not in sitemap)
        3. Combined = maximum page coverage

        Returns:
            Journey object with all captured steps.
        """
        logger.info(f"Starting crawlee crawl: {self.config.target.get('name', 'Unknown')}")
        logger.info(f"Base URL: {self.config.base_url}")
        logger.info(f"Platform: {self.platform.type}")
        logger.info(f"Max pages: {self.config.crawler.max_pages}")

        # Phase 1: Sitemap discovery — find all known URLs upfront
        sitemap = SitemapParser(
            self.config.base_url,
            max_urls=self.config.crawler.max_pages * 2,  # Discover more than we'll crawl
        )
        sitemap_urls = await sitemap.discover_all()

        # Build seed URLs: start URL + sitemap URLs
        seed_urls = [self.config.base_url]
        if sitemap_urls:
            logger.info(f"Sitemap: {len(sitemap_urls)} URLs discovered, seeding crawl queue")
            # Add sitemap URLs (crawlee deduplicates automatically)
            seed_urls.extend(sitemap_urls)
        else:
            logger.info("No sitemap found, relying on link discovery from pages")

        # Phase 2: Smart page selection
        if sitemap_urls:
            selected = PageSelector.select(seed_urls, self.base_domain)
            seed_urls = [s["url"] for s in selected]
            logger.info(f"Smart selection: {len(seed_urls)} pages to capture")

        # Phase 3: Crawl with crawlee
        viewport = self.platform.viewport or {"width": 1920, "height": 1080}

        # use_incognito_pages=True required for WebKit (avoids persistent
        # context which calls CDP setDownloadBehavior — unsupported in WebKit)
        crawler = PlaywrightCrawler(
            max_requests_per_crawl=self.config.crawler.max_pages,
            headless=self.config.crawler.headless,
            browser_type=self.browser_type,
            max_request_retries=self.config.crawler.max_retries,
            use_incognito_pages=True,
        )

        @crawler.router.default_handler
        async def handle_page(context: PlaywrightCrawlingContext) -> None:
            page = context.page
            url = page.url

            # Skip external pages
            if self.base_domain not in urlparse(url).netloc:
                logger.debug(f"Skipping external: {url[:80]}")
                return

            # URL dedup
            normalized = url.split("?")[0].split("#")[0].rstrip("/")
            if normalized in self.captured_urls:
                logger.debug(f"Already captured: {url[:80]}")
                return

            # Get page info for block detection
            title = await page.title() or ""
            try:
                text_preview = await page.evaluate(
                    "document.body?.innerText?.slice(0, 500) || ''"
                )
            except Exception:
                text_preview = ""

            # Block page detection
            if AntiCrawlerDetector.is_block_page(title, text_preview):
                logger.warning(f"Block page detected: {title} at {url[:60]}")
                return

            # Empty page detection
            if AntiCrawlerDetector.is_empty_page(await page.content(), text_preview):
                logger.warning(f"Empty page detected: {url[:60]}")
                return

            self.pages_captured += 1
            self.captured_urls.add(normalized)
            step_num = self.pages_captured

            logger.info(
                f"[{step_num}/{self.config.crawler.max_pages}] "
                f"Captured: {title[:50]} | {url[:60]}"
            )

            # === OUR ANALYSIS LAYER ===

            # 1. Screenshot with PII blur
            screenshot_path = None
            try:
                screenshot_path = await self.screenshot_manager.capture_screenshot(
                    page, step_num
                )
            except Exception as e:
                logger.warning(f"Screenshot failed: {e}")

            # 2. Page analysis (forms, links, buttons, CTAs, navigation)
            page_data = {}
            try:
                page_data = await self.page_analyzer.analyze_page(page)
            except Exception as e:
                logger.warning(f"Page analysis failed: {e}")
                page_data = {"url": url, "title": title}

            # Classify page type
            page_data["page_type"] = PageClassifier.classify_url(url)

            # 3. Compliance data (cookies, localStorage, network, tab order)
            try:
                compliance_data = await self.compliance_collector.collect(
                    page, context.page.context
                )
                page_data.update(compliance_data)
            except Exception as e:
                logger.debug(f"Compliance data collection failed: {e}")

            # 3.5 Design system data (for DS builder)
            try:
                design_data = await self.design_collector.collect(page)
                page_data["css_variables"] = design_data.get("css_variables", {})
                page_data["component_tree"] = design_data.get("component_tree", [])
                page_data["asset_urls"] = design_data.get("asset_urls", {})
                if isinstance(page_data.get("computed_styles"), list):
                    page_data["computed_styles"] = {"text_elements": page_data["computed_styles"]}
                elif not isinstance(page_data.get("computed_styles"), dict):
                    page_data["computed_styles"] = {}
                page_data["computed_styles"]["all_elements"] = design_data.get("all_element_styles", [])
            except Exception as e:
                logger.debug(f"Design data collection failed: {e}")

            # 4. Framework detection
            if self.cdp_detector:
                try:
                    framework = await self.cdp_detector.detect_framework(page)
                    page_data["framework"] = framework
                except Exception:
                    page_data["framework"] = "unknown"

            # 5. Form filling
            try:
                fill_result = await self.form_filler.fill_all_forms(page)
                if fill_result["fields_filled"] > 0:
                    logger.info(f"Filled {fill_result['fields_filled']} form fields")
            except Exception as e:
                logger.debug(f"Form fill failed: {e}")

            # 6. Build journey step
            step = JourneyStep(
                step_number=step_num,
                url=url,
                title=title,
                screenshot_path=screenshot_path,
                page_data=page_data,
            )
            self.journey.add_step(step)

            # 7. Enqueue internal links (crawlee handles dedup)
            try:
                await context.enqueue_links(strategy="same-domain")
            except Exception as e:
                logger.debug(f"Link enqueue failed: {e}")

        # Run the crawl with all seed URLs (sitemap + base URL)
        await crawler.run(seed_urls)

        # Complete journey
        self.journey.complete()

        logger.info(f"Crawl complete: {self.pages_captured} pages captured")

        return self.journey

    def get_stats(self):
        """Get crawler statistics."""
        return {
            "pages_captured": self.pages_captured,
            "engine": "crawlee",
            "captured_urls": len(self.captured_urls),
        }
