"""
Appium-based crawler for native Android/iOS and WebView wrapper apps.

Public interface matches AutonomousCrawler:
    crawler = AppiumCrawler(config, output_dir, platform)
    journey = await crawler.crawl()
    stats   = crawler.get_stats()
"""
import asyncio
import base64
import logging
from pathlib import Path
from typing import Dict

from ux_journey_scraper.core.app_architecture_detector import AppArchitectureDetector
from ux_journey_scraper.core.appium_session import AppiumSession
from ux_journey_scraper.core.gesture_engine import GestureEngine
from ux_journey_scraper.core.journey_recorder import Journey, JourneyStep
from ux_journey_scraper.core.mobile_state_registry import MobileStateRegistry
from ux_journey_scraper.core.native_element_detector import NativeElementDetector

logger = logging.getLogger(__name__)

# Permission dialog allow-button labels
_IOS_ALLOW_LABELS = {"Allow", "OK", "Continue", "Allow While Using App", "Always Allow"}
_ANDROID_PERM_BTN_ID = "com.android.permissioncontroller:id/permission_allow_button"

# Maximum back-navigation attempts before giving up on a dead end
_MAX_BACK_ATTEMPTS = 3


class AppiumCrawler:
    """
    Autonomous crawler for native and WebView mobile apps.

    Reuses Journey / JourneyStep (same output format as AutonomousCrawler) so
    BayMAAR's downstream analyzers work without modification.
    """

    def __init__(self, config, output_dir: str, platform):
        """
        Args:
            config: ScrapeConfig instance
            output_dir: Directory for journey.json and screenshots/
            platform: PlatformConfig with is_native == True
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.platform = platform

        screenshots_dir = self.output_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        self._screenshots_dir = screenshots_dir

        self.state_registry = MobileStateRegistry()
        self.element_detector = NativeElementDetector()
        self.gesture_engine = GestureEngine()
        self.pages_captured = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def crawl(self) -> Journey:
        """
        Crawl the native app and return a Journey.

        Returns:
            Journey with steps populated (same structure as web crawl output)
        """
        session = AppiumSession()
        driver = session.create_driver(self.platform)
        journey = Journey(start_url="", viewport=(0, 0))

        try:
            arch = await AppArchitectureDetector().detect(driver)
            logger.info(
                f"Architecture detected: {arch.architecture} "
                f"(confidence {arch.confidence:.2f}, platform {arch.platform})"
            )

            if arch.architecture == "webview":
                await self._crawl_webview(driver, journey)
            else:
                await self._crawl_native(driver, journey)
        except Exception as exc:
            logger.error(f"AppiumCrawler error: {exc}", exc_info=True)
        finally:
            try:
                driver.quit()
            except Exception:
                pass

        journey.complete()
        return journey

    def get_stats(self) -> Dict:
        """Return crawl statistics (same interface as AutonomousCrawler)."""
        return {
            "pages_captured": self.pages_captured,
            "unique_states": self.state_registry.size(),
        }

    # ------------------------------------------------------------------
    # WebView crawl (Ionic / Capacitor / Cordova)
    # ------------------------------------------------------------------

    async def _crawl_webview(self, driver, journey: Journey) -> None:
        """
        Switch to WebView context and crawl the DOM like a web page.

        Appium exposes all available contexts via driver.contexts.  We look for
        the first WEBVIEW_* context, switch to it, then navigate with standard
        Selenium find_element calls and scroll gestures for infinite-scroll
        detection.
        """
        try:
            contexts = driver.contexts
            webview_ctx = next(
                (c for c in contexts if "WEBVIEW" in c or "CHROMIUM" in c), None
            )
            if not webview_ctx:
                logger.warning("No WebView context found — falling back to native crawl")
                await self._crawl_native(driver, journey)
                return

            logger.info(f"Switching to WebView context: {webview_ctx}")
            try:
                driver.switch_to.context(webview_ctx)
            except Exception as e:
                if "Chromedriver" in str(e) or "chromedriver" in str(e):
                    logger.warning(
                        f"ChromeDriver not available for WebView — falling back to native crawl. "
                        f"Add 'chromedriverAutodownload: true' capability or install ChromeDriver."
                    )
                    await self._crawl_native(driver, journey)
                    return
                raise

            max_pages = self.config.crawler.max_pages
            pages = 0
            consecutive_dupes = 0

            while pages < max_pages:
                screenshot_b64 = driver.get_screenshot_as_base64()

                try:
                    elements = driver.find_elements("css selector", "button, a, [role='button']")
                    element_summary = "|".join(
                        (e.text or "")[:30] for e in elements[:10]
                    )
                except Exception:
                    element_summary = ""

                if self.state_registry.has_seen(screenshot_b64, element_summary):
                    consecutive_dupes += 1
                    if consecutive_dupes >= _MAX_BACK_ATTEMPTS:
                        logger.debug("WebView dead-end after %d dupes", consecutive_dupes)
                        break
                    self.gesture_engine.scroll_down(driver, self.platform.type)
                    await asyncio.sleep(0.5)
                    continue

                consecutive_dupes = 0
                self.state_registry.register(screenshot_b64, element_summary)

                step = await self._capture_screen(driver, pages, "webview-screen")
                journey.steps.append(step)
                pages += 1
                self.pages_captured += 1

                # Try tapping the first visible interactive element
                tapped = False
                for el in elements:
                    try:
                        if el.is_displayed() and el.is_enabled():
                            el.click()
                            await asyncio.sleep(1)
                            tapped = True
                            break
                    except Exception:
                        continue

                if not tapped:
                    self.gesture_engine.scroll_down(driver, self.platform.type)
                    await asyncio.sleep(0.5)

        except Exception as exc:
            logger.error(f"WebView crawl error: {exc}", exc_info=True)

    # ------------------------------------------------------------------
    # Native crawl (React Native, Swift, Kotlin, Flutter)
    # ------------------------------------------------------------------

    async def _crawl_native(self, driver, journey: Journey) -> None:
        """
        Crawl a purely native app via the accessibility tree.

        Flutter apps with semantics disabled are detected heuristically and
        handled in screenshot-only scroll mode.
        """
        max_pages = self.config.crawler.max_pages
        pages = 0
        back_attempts = 0

        while pages < max_pages:
            screenshot_b64 = driver.get_screenshot_as_base64()
            elements = self.element_detector.find_interactive(driver, self.platform.type)
            element_summary = "|".join(e.text for e in elements[:10])

            if self.state_registry.has_seen(screenshot_b64, element_summary):
                back_attempts += 1
                if back_attempts >= _MAX_BACK_ATTEMPTS:
                    logger.debug("Native dead-end — stopping crawl")
                    break
                self.gesture_engine.swipe_back(driver, self.platform.type)
                await asyncio.sleep(0.8)
                continue

            back_attempts = 0
            self.state_registry.register(screenshot_b64, element_summary)

            # Flutter with semantics disabled — screenshot-only scroll mode
            if self.element_detector.is_flutter_only(elements, self.platform.type):
                logger.warning(
                    "Flutter app with semantics disabled — screenshot-only mode"
                )
                step = await self._capture_screen(driver, pages, "flutter-screen")
                journey.steps.append(step)
                pages += 1
                self.pages_captured += 1
                self.gesture_engine.scroll_down(driver, self.platform.type)
                await asyncio.sleep(0.5)
                continue

            # Capture the current screen
            step = await self._capture_screen(driver, pages, "native-screen")
            journey.steps.append(step)
            pages += 1
            self.pages_captured += 1

            # Dismiss any permission dialog before interacting
            await self._handle_permission_dialog(driver)

            if not elements:
                self.gesture_engine.scroll_down(driver, self.platform.type)
                await asyncio.sleep(0.5)
                continue

            # Tap the highest-priority element
            target = elements[0]
            try:
                live_el = driver.find_element("id", target.element_id)
                self.gesture_engine.tap(driver, live_el)
                await asyncio.sleep(1.0)
            except Exception as exc:
                logger.debug(f"Tap failed ({exc}) — navigating back")
                self.gesture_engine.swipe_back(driver, self.platform.type)
                await asyncio.sleep(0.8)

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    async def _handle_permission_dialog(self, driver) -> None:
        """Auto-dismiss OS permission dialogs (camera, location, notifications, etc.)."""
        try:
            if self.platform.type == "native_ios":
                for label in _IOS_ALLOW_LABELS:
                    try:
                        btn = driver.find_element(
                            "xpath",
                            f"//XCUIElementTypeButton[@name='{label}']",
                        )
                        btn.click()
                        logger.debug(f"Dismissed iOS permission dialog: '{label}'")
                        await asyncio.sleep(0.5)
                        return
                    except Exception:
                        continue
            else:
                try:
                    btn = driver.find_element("id", _ANDROID_PERM_BTN_ID)
                    btn.click()
                    logger.debug("Dismissed Android permission dialog")
                    await asyncio.sleep(0.5)
                except Exception:
                    pass
        except Exception as exc:
            logger.debug(f"Permission dialog check error: {exc}")

    async def _capture_screen(self, driver, step_num: int, description: str) -> JourneyStep:
        """
        Capture the current screen and save as a PNG.

        Args:
            driver: Appium WebDriver
            step_num: Zero-based step counter
            description: Human-readable label for the step

        Returns:
            JourneyStep ready to append to Journey.steps
        """
        screenshot_b64 = driver.get_screenshot_as_base64()
        img_bytes = base64.b64decode(screenshot_b64)
        screenshot_path = self._screenshots_dir / f"step-{step_num:03d}.png"

        with open(screenshot_path, "wb") as f:
            f.write(img_bytes)

        return JourneyStep(
            step_number=step_num,
            url="",
            title=description,
            screenshot_path=str(screenshot_path),
            page_data={},
        )
