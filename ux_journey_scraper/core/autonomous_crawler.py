"""
Autonomous crawler - main crawl engine that orchestrates all components.

Integrates:
- Navigation queue (priority-based crawling)
- State registry (deduplication)
- Page readiness (accurate captures)
- Element intelligence (smart clickable detection)
- Form filling (checkout flows)
- Auth management (logged-in crawling)
- Human behavior (anti-bot)
- Session splitting support
- Cookie persistence
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

from ux_journey_scraper.config.scrape_config import PlatformConfig, ScrapeConfig
from ux_journey_scraper.core.auth_manager import AuthManager
from ux_journey_scraper.core.cookie_jar import CookieJar
from ux_journey_scraper.core.element_intelligence import ElementIntelligence
from ux_journey_scraper.core.form_filler import FormFiller
from ux_journey_scraper.core.human_behaviour import HumanBehaviour
from ux_journey_scraper.core.journey_recorder import Journey, JourneyStep
from ux_journey_scraper.core.navigation_behaviour import NavigationBehaviour
from ux_journey_scraper.core.navigation_queue import NavigationAction, NavigationQueue
from ux_journey_scraper.core.page_analyzer import PageAnalyzer
from ux_journey_scraper.core.page_readiness import PageReadinessEngine
from ux_journey_scraper.core.screenshot_manager import ScreenshotManager
from ux_journey_scraper.core.session_planner import VisitPlan
from ux_journey_scraper.core.state_registry import StateRegistry
from ux_journey_scraper.core.stealth_browser import create_stealth_browser

logger = logging.getLogger(__name__)


class AutonomousCrawler:
    """Autonomous web crawler with intelligent navigation."""

    def __init__(
        self,
        config: ScrapeConfig,
        output_dir: str = "journey_output",
        visit_plan: Optional[VisitPlan] = None,
        cookie_jar: Optional[CookieJar] = None,
        proxy_override: Optional[Dict] = None,
        platform: Optional[PlatformConfig] = None,
        auth_state: Optional[str] = None,
    ):
        """
        Initialize autonomous crawler.

        Args:
            config: Scrape configuration
            output_dir: Output directory for screenshots and data
            visit_plan: Optional visit plan (for session-split mode)
            cookie_jar: Optional cookie jar for persistence across sessions
            proxy_override: Optional proxy config override
            platform: Optional platform config (for continuous mode)
            auth_state: Optional auth state (for continuous mode)
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Session splitting support
        self.visit_plan = visit_plan
        self.cookie_jar = cookie_jar
        self.proxy_override = proxy_override

        # Platform and auth (for both modes)
        if visit_plan:
            # Split mode: get from visit plan
            self.platform = visit_plan.platform
            self.auth_state = visit_plan.auth_state
            self.max_pages = visit_plan.max_pages
            self.target_page_types = visit_plan.target_page_types
        else:
            # Continuous mode: get from parameters or config
            self.platform = platform or config.platforms[0]
            self.auth_state = auth_state or "logged_out"
            self.max_pages = config.crawler.max_pages
            self.target_page_types = []

        # Initialize components
        self.nav_queue = NavigationQueue(max_depth=config.crawler.max_depth)
        self.state_registry = StateRegistry()
        self.readiness_engine = PageReadinessEngine(
            timeout_ms=config.crawler.timeout_per_page_ms
        )
        self.element_intelligence = ElementIntelligence()
        self.human = HumanBehaviour()
        self.nav_behaviour = NavigationBehaviour()
        self.screenshot_manager = ScreenshotManager(
            output_dir=self.output_dir / "screenshots",
            blur_pii=True,
        )
        self.page_analyzer = PageAnalyzer()
        self.auth_manager = AuthManager(config.auth)
        self.form_filler = FormFiller(config.form_fill)

        # Crawl state
        self.journey: Optional[Journey] = None
        self.current_step = 0
        self.pages_captured = 0
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def crawl(self) -> Journey:
        """
        Start autonomous crawl.

        Returns:
            Journey object with all captured steps
        """
        session_id = self.visit_plan.session_id if self.visit_plan else "continuous"
        logger.info(f"Starting crawl: {session_id} on {self.platform.type}")
        logger.info(f"Base URL: {self.config.base_url}")
        logger.info(f"Max pages: {self.max_pages}")
        logger.info(f"Auth state: {self.auth_state}")

        # Initialize journey
        self.journey = Journey(
            start_url=self.config.base_url,
            viewport=(
                self.platform.viewport["width"],
                self.platform.viewport["height"],
            ),
            platform_type=self.platform.type,
            user_agent=self.platform.user_agent,
        )

        try:
            # Launch stealth browser (routes to local or cloud)
            self.playwright, self.browser, self.context = await create_stealth_browser(
                config=self.config,
                platform=self.platform,
                proxy_override=self.proxy_override,
            )

            # Inject cookies if available (returning visitor simulation)
            if self.cookie_jar:
                domain = urlparse(self.config.base_url).netloc
                cookies = self.cookie_jar.get(domain)
                if cookies:
                    await self.context.add_cookies(cookies)
                    logger.info(f"Injected {len(cookies)} cookies (returning visitor)")

            self.page = await self.context.new_page()

            # Authenticate if needed
            if self.auth_state == "logged_in":
                auth_success = await self.auth_manager.ensure_authenticated(self.page)
                if not auth_success:
                    raise RuntimeError("Authentication failed")

            # Initialize navigation queue
            entry_url = (
                self.visit_plan.entry_url if self.visit_plan else self.config.base_url
            )
            self.nav_queue.add(
                NavigationAction(
                    type="navigate",
                    priority=100,
                    depth=0,
                    url=entry_url,
                )
            )

            # Add seed URLs with lower priority (explore options)
            for seed_url in self.config.seed_urls:
                if seed_url != entry_url:
                    self.nav_queue.add(
                        NavigationAction(
                            type="navigate",
                            priority=80,
                            depth=0,
                            url=seed_url,
                        )
                    )

            # Main crawl loop
            await self._crawl_loop()

            # Complete journey
            self.journey.complete()

            logger.info(f"Crawl complete: {self.pages_captured} pages captured")

            return self.journey

        finally:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

    async def _crawl_loop(self) -> None:
        """Main crawl loop - process navigation queue until empty or limit reached."""
        while self.pages_captured < self.max_pages:
            # Get next action
            action = self.nav_queue.next()
            if not action:
                logger.info("Navigation queue exhausted")
                break

            logger.info(
                f"[{self.pages_captured + 1}/{self.max_pages}] "
                f"Processing action: {action.type} (priority={action.priority}, depth={action.depth})"
            )

            try:
                # Execute action
                success = await self._execute_action(action)

                if not success:
                    logger.warning(f"Action failed: {action}")
                    continue

                # Wait for page readiness
                ready = await self.readiness_engine.wait_until_ready(self.page)
                if not ready:
                    logger.warning("Page readiness timeout, capturing anyway")

                # Check for auth wall
                if await self.auth_manager.detect_auth_wall(self.page):
                    logger.warning("Auth wall detected, attempting recovery")
                    recovered = await self.auth_manager.recover_from_auth_wall(
                        self.page
                    )
                    if not recovered:
                        logger.error("Auth recovery failed, skipping page")
                        continue

                # Get current state
                dom_content = await self.page.content()
                current_url = self.page.url

                # Check if this is a new state
                if not self.state_registry.is_new_state(current_url, dom_content):
                    logger.debug("Duplicate state detected, skipping capture")
                    continue

                # Capture screen
                await self._capture_screen()
                self.pages_captured += 1

                # Analyze page type for navigation behaviour
                page_data = await self.page_analyzer.analyze_page(self.page)
                page_type = page_data.get("page_type", "unknown")

                # Simulate realistic page reading time
                await self.nav_behaviour.simulate_page_reading(self.page, page_type)

                # Fill forms if present
                fill_result = await self.form_filler.fill_all_forms(self.page)
                if fill_result["fields_filled"] > 0:
                    logger.info(f"Filled {fill_result['fields_filled']} form fields")

                    # If form filled, wait and capture updated state
                    await asyncio.sleep(1)
                    if self.state_registry.is_new_state(
                        current_url, await self.page.content()
                    ):
                        await self._capture_screen()
                        self.pages_captured += 1

                # Random browsing behaviors (anti-detection)
                # Backtrack occasionally
                await self.nav_behaviour.maybe_backtrack(self.page)

                # Revisit homepage occasionally
                await self.nav_behaviour.maybe_revisit_home(
                    self.page, self.config.base_url
                )

                # Scroll without clicking sometimes
                await self.nav_behaviour.maybe_scroll_without_clicking(self.page)

                # Long pause occasionally
                await self.nav_behaviour.maybe_long_pause()

                # Find new clickables
                clickables = await self.element_intelligence.find_all_clickables(
                    self.page,
                    in_viewport_only=False,
                    max_elements=100,
                )

                # Add clickables to navigation queue
                added = 0
                for clickable in clickables:
                    # Create navigation action
                    new_action = NavigationAction(
                        type="click",
                        priority=clickable["priority"],
                        depth=action.depth + 1,
                        url=current_url,
                        selector=self._generate_selector(clickable),
                        metadata=clickable,
                    )

                    if self.nav_queue.add(new_action):
                        added += 1

                logger.debug(f"Added {added} new actions to queue")

                # Human delay before next action
                await self.human.human_delay(
                    self.config.crawler.delay_ms,
                    self.config.crawler.delay_ms + self.config.crawler.delay_jitter_ms,
                    reason="page_load",
                )

            except Exception as e:
                logger.error(f"Error processing action: {e}")
                continue

    async def _execute_action(self, action: NavigationAction) -> bool:
        """
        Execute a navigation action.

        Args:
            action: NavigationAction to execute

        Returns:
            True if action succeeded
        """
        try:
            if action.type == "navigate":
                await self.page.goto(
                    action.url, timeout=self.config.crawler.timeout_per_page_ms
                )
                return True

            elif action.type == "click":
                # Get element center for human click
                center = await self.element_intelligence.get_element_center(
                    self.page, action.selector
                )

                if not center:
                    logger.warning(f"Element not found: {action.selector}")
                    return False

                # Human-like click
                await self.human.human_click(self.page, center[0], center[1])
                return True

            else:
                logger.warning(f"Unknown action type: {action.type}")
                return False

        except Exception as e:
            logger.error(f"Action execution error: {e}")
            return False

    async def _capture_screen(self) -> None:
        """Capture current page state as a journey step."""
        self.current_step += 1

        logger.debug(f"Capturing screen {self.current_step}...")

        try:
            # Capture screenshot
            screenshot_path = await self.screenshot_manager.capture_screenshot(
                self.page, self.current_step
            )

            # Analyze page
            page_data = await self.page_analyzer.analyze_page(self.page)

            # Create step
            step = JourneyStep(
                step_number=self.current_step,
                url=self.page.url,
                title=await self.page.title(),
                screenshot_path=screenshot_path,
                page_data=page_data,
            )

            # Add to journey
            self.journey.add_step(step)

            logger.info(f"✓ Step {self.current_step} captured: {step.title}")

        except Exception as e:
            logger.error(f"Error capturing screen: {e}")

    def _generate_selector(self, clickable: Dict) -> str:
        """
        Generate CSS selector for clickable element.

        Args:
            clickable: Clickable element dict

        Returns:
            CSS selector string
        """
        # Prefer ID
        if clickable.get("id"):
            return f"#{clickable['id']}"

        # Use stored selector
        if clickable.get("selector"):
            return clickable["selector"]

        # Fallback to tag
        return clickable.get("tag", "div")

    def get_stats(self) -> Dict:
        """
        Get crawler statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "pages_captured": self.pages_captured,
            "current_step": self.current_step,
            "queue_stats": self.nav_queue.get_stats(),
            "state_stats": self.state_registry.get_stats(),
        }

    async def get_cookies(self) -> List[Dict]:
        """
        Get current cookies from browser context.
        Used by CrawlOrchestrator to persist cookies across sessions.

        Returns:
            List of cookie dicts
        """
        if not self.context:
            return []

        try:
            cookies = await self.context.cookies()
            return cookies
        except Exception as e:
            logger.warning(f"Failed to get cookies: {e}")
            return []
