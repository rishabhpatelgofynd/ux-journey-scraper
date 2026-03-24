"""
Realistic navigation behavior for anti-detection.

Adds human-like randomness to the crawl path: variable reading times,
backtracking, homepage revisits, random pauses, gentle scrolling.
"""

import asyncio
import logging
import random
from typing import Optional

from playwright.async_api import Page

logger = logging.getLogger(__name__)


# Variable reading time per page type (seconds)
# Real users spend different amounts of time on different pages
PAGE_READ_TIME = {
    "home": (3, 8),
    "plp": (5, 15),  # Scrolls, compares products
    "pdp": (8, 30),  # Reads description, checks reviews, zooms images
    "cart": (3, 10),
    "checkout": (10, 45),  # Address entry, payment selection
    "confirmation": (5, 12),
    "search": (2, 5),
    "login": (3, 8),
    "account": (3, 8),
    "orders": (5, 12),
    "order_detail": (5, 15),
    "tracking": (3, 8),
    "returns": (5, 12),
    "wishlist": (3, 8),
    "unknown": (3, 10),
}


class NavigationBehaviour:
    """
    Adds human-like randomness to the crawl path.
    Called between page captures to simulate realistic browsing.

    Key insight: real users don't visit pages in a perfect linear sequence.
    They backtrack, revisit, scroll without clicking, get distracted.
    """

    def __init__(self):
        """Initialize navigation behavior tracker."""
        self._consecutive_forward = 0  # Track linear navigation depth

    async def simulate_page_reading(self, page: Page, page_type: str):
        """
        Simulate time spent reading the current page.
        Called AFTER screenshot/DOM capture (data is already collected).
        This is purely for anti-detection — the delay makes the session look natural.

        Args:
            page: Playwright page
            page_type: Type of page (home, pdp, cart, etc.)
        """
        min_sec, max_sec = PAGE_READ_TIME.get(page_type, (3, 10))
        read_time = random.uniform(min_sec, max_sec)

        logger.debug(f"Simulating {read_time:.1f}s reading time on {page_type}")

        # During reading time, do natural things
        elapsed = 0
        while elapsed < read_time:
            action_time = random.uniform(0.5, 2.0)

            roll = random.random()
            if roll < 0.4:
                # 40% — scroll a bit
                await self._gentle_scroll(page)
            elif roll < 0.6:
                # 20% — mouse wander
                await self._mouse_wander(page)
            else:
                # 40% — just wait (reading)
                pass

            await asyncio.sleep(action_time)
            elapsed += action_time

    async def maybe_backtrack(self, page: Page, probability: float = 0.12) -> bool:
        """
        12% chance to hit the back button.
        Real users do this when a page isn't what they expected.

        Args:
            page: Playwright page
            probability: Probability of backtracking (0-1)

        Returns:
            True if backtrack happened
        """
        if random.random() > probability:
            return False

        try:
            await page.go_back(wait_until="domcontentloaded", timeout=10000)
            self._consecutive_forward = 0
            logger.debug("NavigationBehaviour: backtracked")
            return True

        except Exception as e:
            logger.debug(f"Backtrack failed: {e}")
            return False

    async def maybe_revisit_home(
        self, page: Page, base_url: str, probability: float = 0.06
    ) -> bool:
        """
        6% chance to navigate back to homepage.
        Real users do this to "reset" their browsing.

        Args:
            page: Playwright page
            base_url: Site base URL (homepage)
            probability: Probability of revisiting home (0-1)

        Returns:
            True if homepage revisit happened
        """
        if random.random() > probability:
            return False

        try:
            await page.goto(base_url, wait_until="domcontentloaded", timeout=15000)
            self._consecutive_forward = 0
            logger.debug("NavigationBehaviour: revisited homepage")
            return True

        except Exception as e:
            logger.debug(f"Homepage revisit failed: {e}")
            return False

    async def maybe_long_pause(self, probability: float = 0.08):
        """
        8% chance of a 15-45 second pause.
        Simulates: user got distracted, checked phone, read something carefully.

        Args:
            probability: Probability of long pause (0-1)
        """
        if random.random() > probability:
            return

        pause = random.uniform(15, 45)
        logger.debug(f"NavigationBehaviour: long pause {pause:.0f}s")
        await asyncio.sleep(pause)

    async def maybe_scroll_without_clicking(
        self, page: Page, probability: float = 0.15
    ) -> bool:
        """
        15% chance to scroll the whole page but not click anything.
        User looked but nothing caught their eye.

        Args:
            page: Playwright page
            probability: Probability of scrolling (0-1)

        Returns:
            True if scrolling happened
        """
        if random.random() > probability:
            return False

        try:
            # Scroll to bottom in chunks
            viewport_height = (
                page.viewport_size.get("height", 900) if page.viewport_size else 900
            )
            scroll_steps = random.randint(3, 6)

            for _ in range(scroll_steps):
                await page.mouse.wheel(0, viewport_height // 2)
                await asyncio.sleep(random.uniform(0.5, 1.5))

            logger.debug("NavigationBehaviour: scrolled page without clicking")
            return True

        except Exception as e:
            logger.debug(f"Scroll without clicking failed: {e}")
            return False

    async def _gentle_scroll(self, page: Page):
        """
        Small scroll — not the full page, just a bit of reading.

        Args:
            page: Playwright page
        """
        try:
            delta = random.randint(100, 400)
            await page.mouse.wheel(0, delta)

        except Exception:
            pass  # Silently fail

    async def _mouse_wander(self, page: Page):
        """
        Random mouse movement within viewport.

        Args:
            page: Playwright page
        """
        try:
            viewport = page.viewport_size or {"width": 1440, "height": 900}
            x = random.randint(100, viewport["width"] - 100)
            y = random.randint(100, viewport["height"] - 100)
            await page.mouse.move(x, y)

        except Exception:
            pass  # Silently fail

    def increment_forward(self):
        """Track consecutive forward navigations."""
        self._consecutive_forward += 1

    def get_consecutive_forward(self) -> int:
        """
        Get count of consecutive forward navigations.

        Returns:
            Number of consecutive forward navigations
        """
        return self._consecutive_forward

    def reset(self):
        """Reset behavior tracking (for new session)."""
        self._consecutive_forward = 0
        logger.debug("NavigationBehaviour reset")

    async def simulate_realistic_delay(self, base_delay_ms: int, jitter_ms: int):
        """
        Add realistic delay with jitter.

        Args:
            base_delay_ms: Base delay in milliseconds
            jitter_ms: Maximum random jitter to add
        """
        total_delay = base_delay_ms + random.randint(0, jitter_ms)
        await asyncio.sleep(total_delay / 1000)

    async def simulate_form_thinking_time(self, field_type: str = "text"):
        """
        Simulate time user spends thinking before filling a form field.

        Args:
            field_type: Type of field (text, email, select, etc.)
        """
        # Different fields require different thinking times
        thinking_times = {
            "text": (0.5, 2.0),
            "email": (1.0, 3.0),
            "password": (1.0, 2.5),
            "select": (0.5, 1.5),
            "checkbox": (0.3, 0.8),
            "radio": (0.3, 0.8),
            "textarea": (2.0, 5.0),
        }

        min_sec, max_sec = thinking_times.get(field_type, (0.5, 2.0))
        think_time = random.uniform(min_sec, max_sec)

        await asyncio.sleep(think_time)
