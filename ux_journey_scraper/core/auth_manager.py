"""
Authentication and session management for logged-in crawling.

Supports:
- Session save/load (cookies + localStorage)
- Login flow automation
- Auth wall detection
- Mid-crawl auth recovery
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional

from ux_journey_scraper.config.scrape_config import AuthConfig

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication state during crawling."""

    def __init__(self, auth_config: AuthConfig):
        """
        Initialize auth manager.

        Args:
            auth_config: Authentication configuration
        """
        self.config = auth_config
        self.is_authenticated = False

    async def ensure_authenticated(self, page) -> bool:
        """
        Ensure page is authenticated (try session first, fall back to login).

        Args:
            page: Playwright page object

        Returns:
            True if authenticated successfully
        """
        if not self.config.logged_in:
            logger.debug("Auth not required (logged_out mode)")
            return True

        logger.info("Ensuring authentication...")

        # Strategy 1: Try session injection
        if self.config.session_file and Path(self.config.session_file).exists():
            logger.debug("Attempting session restoration...")
            if await self._load_session(page):
                # Verify session is still valid
                if await self._verify_auth(page):
                    logger.info("Session restored successfully")
                    self.is_authenticated = True
                    return True
                else:
                    logger.warning("Saved session expired, will login fresh")

        # Strategy 2: Full login flow
        if self.config.credentials:
            logger.info("Starting login flow...")
            success = await self._perform_login(page)

            if success:
                # Save session for next time
                if self.config.session_file:
                    await self._save_session(page)

                self.is_authenticated = True
                return True

        logger.error("Authentication failed")
        return False

    async def _load_session(self, page) -> bool:
        """
        Load session from file (cookies + localStorage).

        Args:
            page: Playwright page

        Returns:
            True if session loaded successfully
        """
        try:
            with open(self.config.session_file, "r") as f:
                session_data = json.load(f)

            # Load cookies
            if "cookies" in session_data:
                await page.context.add_cookies(session_data["cookies"])
                logger.debug(f"Loaded {len(session_data['cookies'])} cookies")

            # Navigate to site first
            if self.config.login_success_indicator:
                # Navigate to a page that would show auth status
                base_url = self._extract_base_url(self.config.login_url)
                await page.goto(base_url)

            # Load localStorage
            if "localStorage" in session_data:
                await page.evaluate(
                    """
                    (storage) => {
                        for (const [key, value] of Object.entries(storage)) {
                            localStorage.setItem(key, value);
                        }
                    }
                    """,
                    session_data["localStorage"],
                )
                logger.debug(
                    f"Loaded {len(session_data['localStorage'])} localStorage items"
                )

            return True

        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return False

    async def _save_session(self, page) -> None:
        """
        Save session to file (cookies + localStorage).

        Args:
            page: Playwright page
        """
        try:
            # Get cookies
            cookies = await page.context.cookies()

            # Get localStorage
            local_storage = await page.evaluate("() => ({ ...localStorage })")

            # Save to file
            session_data = {
                "cookies": cookies,
                "localStorage": local_storage,
            }

            Path(self.config.session_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config.session_file, "w") as f:
                json.dump(session_data, f, indent=2)

            logger.info(f"Session saved to: {self.config.session_file}")

        except Exception as e:
            logger.error(f"Error saving session: {e}")

    async def _perform_login(self, page) -> bool:
        """
        Perform full login flow.

        Args:
            page: Playwright page

        Returns:
            True if login successful
        """
        try:
            # Navigate to login page
            await page.goto(self.config.login_url)
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Wait a bit for page to stabilize
            await asyncio.sleep(1)

            # Find and fill username/email field
            username_filled = await self._fill_field(
                page,
                [
                    'input[type="email"]',
                    'input[type="text"][name*="user"]',
                    'input[type="text"][name*="email"]',
                    'input[name="username"]',
                    'input[id*="user"]',
                    'input[id*="email"]',
                ],
                self.config.credentials.get("username")
                or self.config.credentials.get("email", ""),
            )

            if not username_filled:
                logger.error("Could not find username/email field")
                return False

            # Find and fill password field
            password_filled = await self._fill_field(
                page,
                [
                    'input[type="password"]',
                    'input[name="password"]',
                    'input[id*="pass"]',
                ],
                self.config.credentials.get("password", ""),
            )

            if not password_filled:
                logger.error("Could not find password field")
                return False

            # Find and click submit button
            submit_clicked = await self._click_submit(page)

            if not submit_clicked:
                logger.error("Could not find submit button")
                return False

            # Wait for login to complete
            await self._wait_for_login_success(page)

            # Verify authentication
            return await self._verify_auth(page)

        except Exception as e:
            logger.error(f"Login flow error: {e}")
            return False

    async def _fill_field(
        self,
        page,
        selectors: list[str],
        value: str,
    ) -> bool:
        """
        Find and fill a form field.

        Args:
            page: Playwright page
            selectors: List of possible selectors to try
            value: Value to fill

        Returns:
            True if filled successfully
        """
        for selector in selectors:
            try:
                field = await page.query_selector(selector)
                if field and await field.is_visible():
                    await field.click()
                    await asyncio.sleep(0.1)
                    await field.fill(value)
                    logger.debug(f"Filled field: {selector}")
                    return True
            except Exception:
                continue

        return False

    async def _click_submit(self, page) -> bool:
        """
        Find and click login submit button.

        Args:
            page: Playwright page

        Returns:
            True if clicked successfully
        """
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'button:has-text("Submit")',
        ]

        for selector in submit_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    await button.click()
                    logger.debug(f"Clicked submit: {selector}")
                    return True
            except Exception:
                continue

        return False

    async def _wait_for_login_success(self, page) -> None:
        """
        Wait for login to complete.

        Args:
            page: Playwright page
        """
        try:
            # Wait for navigation or indicator
            await page.wait_for_load_state("networkidle", timeout=10000)
            await asyncio.sleep(2)  # Extra buffer
        except Exception:
            pass

    async def _verify_auth(self, page) -> bool:
        """
        Verify that authentication succeeded.

        Args:
            page: Playwright page

        Returns:
            True if authenticated
        """
        if not self.config.login_success_indicator:
            logger.warning("No login_success_indicator configured, assuming success")
            return True

        try:
            # Check if indicator is URL-based
            if self.config.login_success_indicator.startswith("/"):
                # URL path indicator
                current_url = page.url
                return self.config.login_success_indicator in current_url

            else:
                # CSS selector indicator
                element = await page.query_selector(self.config.login_success_indicator)
                if element:
                    is_visible = await element.is_visible()
                    logger.debug(f"Auth indicator visible: {is_visible}")
                    return is_visible

                return False

        except Exception as e:
            logger.error(f"Auth verification error: {e}")
            return False

    async def detect_auth_wall(self, page) -> bool:
        """
        Detect if we've hit an auth wall mid-crawl.

        Args:
            page: Playwright page

        Returns:
            True if auth wall detected
        """
        url = page.url.lower()

        # Check for common auth wall URLs
        auth_wall_patterns = [
            "/login",
            "/signin",
            "/sign-in",
            "/auth",
            "/authenticate",
        ]

        for pattern in auth_wall_patterns:
            if pattern in url:
                logger.warning(f"Auth wall detected: {url}")
                return True

        return False

    async def recover_from_auth_wall(self, page) -> bool:
        """
        Attempt to recover from mid-crawl auth loss.

        Args:
            page: Playwright page

        Returns:
            True if recovery successful
        """
        logger.info("Attempting auth recovery...")

        # Try re-authentication
        return await self.ensure_authenticated(page)

    def _extract_base_url(self, url: str) -> str:
        """
        Extract base URL (protocol + domain) from full URL.

        Args:
            url: Full URL

        Returns:
            Base URL
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
