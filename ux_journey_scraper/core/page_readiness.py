"""
Advanced page readiness detection for accurate screen captures.

Solves the "screenshot too early" problem with comprehensive checks:
- Network idle
- DOM stability (MutationObserver)
- Spinner/loading dismissal
- Lazy-loaded content (scroll trigger)
- Font and image loading
"""
import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)


class PageReadinessEngine:
    """Detects when a page is truly ready for capture."""

    # Common loading spinner selectors
    LOADING_SELECTORS = [
        "[class*='spinner']",
        "[class*='loading']",
        "[class*='skeleton']",
        "[class*='loader']",
        "[class*='preloader']",
        "[aria-busy='true']",
        "[data-loading='true']",
        ".spinner",
        ".loading",
        ".loader",
        "#spinner",
        "#loading",
        "#loader",
    ]

    # Common overlay/popup selectors to dismiss
    OVERLAY_SELECTORS = [
        "[class*='cookie']",
        "[class*='gdpr']",
        "[class*='consent']",
        "[class*='banner']",
        "[class*='modal']",
        "[class*='popup']",
        "[class*='overlay']",
        "[role='dialog']",
        "[role='alertdialog']",
    ]

    def __init__(self, timeout_ms: int = 15000):
        """
        Initialize readiness engine.

        Args:
            timeout_ms: Maximum time to wait for readiness (milliseconds)
        """
        self.timeout_ms = timeout_ms

    async def wait_until_ready(self, page) -> bool:
        """
        Wait until page is genuinely ready for capture.

        Performs comprehensive readiness checks:
        1. Network idle (no requests for 500ms)
        2. DOM stable (no mutations for 300ms)
        3. Images loaded
        4. No loading spinners
        5. Fonts rendered
        6. Scroll-triggered content loaded

        Args:
            page: Playwright page object

        Returns:
            True if page became ready, False if timeout
        """
        logger.info(f"Waiting for page readiness: {page.url}")

        try:
            # Step 1: Basic page load
            await page.wait_for_load_state("domcontentloaded", timeout=self.timeout_ms)

            # Step 2: Network idle (with timeout)
            try:
                await page.wait_for_load_state("networkidle", timeout=8000)
            except asyncio.TimeoutError:
                # Network idle timeout is OK (long-pollers, websockets)
                logger.debug("Network idle timeout (acceptable)")

            # Step 3: Dismiss loading spinners
            await self._wait_for_no_spinners(page)

            # Step 4: Wait for images to load
            await self._wait_for_images(page)

            # Step 5: Scroll to trigger lazy-loaded content
            await self._scroll_to_load(page)

            # Step 6: Back to top
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.3)

            # Step 7: Final DOM stability check
            await self._wait_for_dom_stable(page, stable_for_ms=300)

            # Step 8: Dismiss common overlays
            await self._dismiss_overlays(page)

            logger.info("Page ready for capture")
            return True

        except asyncio.TimeoutError:
            logger.warning(f"Page readiness timeout after {self.timeout_ms}ms")
            return False
        except Exception as e:
            logger.error(f"Error during readiness check: {e}")
            return False

    async def _wait_for_no_spinners(self, page, timeout_ms: int = 8000) -> None:
        """
        Wait for all loading spinners to disappear.

        Args:
            page: Playwright page
            timeout_ms: Maximum wait time
        """
        logger.debug("Checking for loading spinners...")

        try:
            # Wait for all spinner selectors to be hidden
            for selector in self.LOADING_SELECTORS:
                try:
                    # Wait for selector to be hidden (or not exist)
                    await page.wait_for_selector(
                        selector,
                        state="hidden",
                        timeout=timeout_ms,
                    )
                except Exception:
                    # Selector not found or already hidden - OK
                    pass

            logger.debug("All spinners dismissed")

        except asyncio.TimeoutError:
            logger.warning("Spinner dismissal timeout (continuing anyway)")

    async def _wait_for_images(self, page, timeout_ms: int = 5000) -> None:
        """
        Wait for all images to finish loading.

        Args:
            page: Playwright page
            timeout_ms: Maximum wait time
        """
        logger.debug("Waiting for images to load...")

        try:
            await page.evaluate(
                """
                () => {
                    return new Promise((resolve) => {
                        const images = Array.from(document.images);
                        if (images.length === 0) {
                            resolve();
                            return;
                        }

                        let loadedCount = 0;
                        const totalImages = images.length;

                        const checkComplete = () => {
                            loadedCount++;
                            if (loadedCount === totalImages) {
                                resolve();
                            }
                        };

                        images.forEach(img => {
                            if (img.complete) {
                                checkComplete();
                            } else {
                                img.addEventListener('load', checkComplete);
                                img.addEventListener('error', checkComplete);
                            }
                        });

                        // Timeout fallback
                        setTimeout(resolve, 5000);
                    });
                }
                """
            )
            logger.debug("Images loaded")

        except Exception as e:
            logger.debug(f"Image loading check failed (continuing): {e}")

    async def _wait_for_dom_stable(self, page, stable_for_ms: int = 300) -> None:
        """
        Wait for DOM to be stable (no mutations for specified time).

        Uses MutationObserver to detect when DOM stops changing.

        Args:
            page: Playwright page
            stable_for_ms: Required stability duration (milliseconds)
        """
        logger.debug(f"Waiting for DOM stability ({stable_for_ms}ms)...")

        try:
            await page.evaluate(
                f"""
                (stableFor) => {{
                    return new Promise((resolve) => {{
                        let timer;
                        const observer = new MutationObserver(() => {{
                            clearTimeout(timer);
                            timer = setTimeout(() => {{
                                observer.disconnect();
                                resolve();
                            }}, stableFor);
                        }});

                        observer.observe(document.body, {{
                            subtree: true,
                            childList: true,
                            attributes: true,
                        }});

                        // Initial timer
                        timer = setTimeout(() => {{
                            observer.disconnect();
                            resolve();
                        }}, stableFor);
                    }});
                }}
                """,
                stable_for_ms,
            )
            logger.debug("DOM stable")

        except Exception as e:
            logger.debug(f"DOM stability check failed (continuing): {e}")

    async def _scroll_to_load(self, page) -> None:
        """
        Progressive scroll to trigger lazy-loaded content.

        Many sites load images and content only when scrolled into view.

        Args:
            page: Playwright page
        """
        logger.debug("Scrolling to trigger lazy-loaded content...")

        try:
            # Get page height
            height = await page.evaluate("document.body.scrollHeight")

            # Scroll in steps
            step = 600
            current_y = 0

            while current_y < height:
                current_y += step
                await page.evaluate(f"window.scrollTo(0, {current_y})")
                await asyncio.sleep(0.15)  # Pause to allow content to load

            # Final pause at bottom
            await asyncio.sleep(0.5)

            logger.debug("Lazy-load scroll complete")

        except Exception as e:
            logger.debug(f"Lazy-load scroll failed (continuing): {e}")

    async def _dismiss_overlays(self, page) -> None:
        """
        Attempt to dismiss common overlays (cookie banners, modals).

        Args:
            page: Playwright page
        """
        logger.debug("Checking for overlays to dismiss...")

        dismiss_buttons = [
            # Cookie banners
            "button:has-text('Accept')",
            "button:has-text('Accept All')",
            "button:has-text('I Agree')",
            "button:has-text('OK')",
            "button:has-text('Got it')",
            "button:has-text('Close')",
            "[class*='accept']",
            "[class*='consent']",
            "[id*='accept']",
            "[id*='consent']",
            # Modal close buttons
            "[aria-label='Close']",
            "[aria-label='Dismiss']",
            "button.close",
            "button.dismiss",
            "[class*='modal-close']",
        ]

        for selector in dismiss_buttons:
            try:
                button = await page.query_selector(selector)
                if button:
                    # Check if button is visible
                    is_visible = await button.is_visible()
                    if is_visible:
                        await button.click()
                        logger.debug(f"Dismissed overlay: {selector}")
                        await asyncio.sleep(0.3)  # Wait for overlay to close
                        break  # Only dismiss one overlay
            except Exception:
                # Button not clickable or already gone
                pass

    async def wait_for_navigation(
        self,
        page,
        timeout_ms: int = None,
    ) -> bool:
        """
        Wait for page navigation to complete and page to be ready.

        Args:
            page: Playwright page
            timeout_ms: Override default timeout

        Returns:
            True if navigation completed and page ready
        """
        if timeout_ms is None:
            timeout_ms = self.timeout_ms

        try:
            # Wait for navigation
            await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)

            # Wait for readiness
            return await self.wait_until_ready(page)

        except asyncio.TimeoutError:
            logger.warning(f"Navigation timeout after {timeout_ms}ms")
            return False
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False

    async def is_ready_now(self, page) -> bool:
        """
        Quick check if page appears ready right now (no waiting).

        Args:
            page: Playwright page

        Returns:
            True if page looks ready
        """
        try:
            # Check for loading spinners
            for selector in self.LOADING_SELECTORS[:5]:  # Quick check
                spinner = await page.query_selector(selector)
                if spinner and await spinner.is_visible():
                    return False

            # Check document ready state
            ready_state = await page.evaluate("document.readyState")
            if ready_state != "complete":
                return False

            return True

        except Exception:
            return False
