"""
Proxy IP rotation manager.

Manages proxy IP rotation across visit sessions for anti-detection.
"""

import logging
import os
from typing import Dict, List, Optional

from ..config.scrape_config import ProxySettings

logger = logging.getLogger(__name__)


class ProxyRotator:
    """
    Manages proxy IP rotation across visit sessions.

    For residential rotating proxies (e.g., Bright Data, Oxylabs):
    - The provider rotates IPs per connection automatically
    - pool_size just controls how many "sticky" sessions we maintain

    For static proxy lists:
    - pool is a list of endpoints
    - next() cycles through them round-robin
    """

    def __init__(self, config: ProxySettings):
        """
        Initialize proxy rotator.

        Args:
            config: Proxy settings from scrape config
        """
        self.config = config
        self._pool = self._build_pool(config)
        self._current_index = 0

        if self._pool:
            logger.info(
                f"ProxyRotator initialized: {len(self._pool)} endpoints, "
                f"provider={config.provider}"
            )
        else:
            logger.info("ProxyRotator: proxy disabled")

    def get_for_slot(self, slot: int) -> Optional[Dict[str, str]]:
        """
        Get proxy config for a specific slot (from VisitPlan.proxy_slot).

        Args:
            slot: Slot number to get proxy for

        Returns:
            Proxy config dict for Playwright, or None if proxy disabled
        """
        if not self._pool:
            return None

        endpoint = self._pool[slot % len(self._pool)]
        logger.debug(f"Proxy for slot {slot}: {self._sanitize_url(endpoint)}")

        return {"server": endpoint}

    def next(self) -> Optional[Dict[str, str]]:
        """
        Get next proxy in rotation.

        Returns:
            Proxy config dict for Playwright, or None if proxy disabled
        """
        if not self._pool:
            return None

        proxy = self._pool[self._current_index % len(self._pool)]
        self._current_index += 1

        logger.debug(
            f"Next proxy: {self._sanitize_url(proxy)} (index {self._current_index - 1})"
        )

        return {"server": proxy}

    def reset(self):
        """Reset rotation to start from first proxy."""
        self._current_index = 0
        logger.debug("Proxy rotation reset to index 0")

    def _build_pool(self, config: ProxySettings) -> List[str]:
        """
        Build pool of proxy endpoints.

        Args:
            config: Proxy settings

        Returns:
            List of proxy endpoint URLs
        """
        if not config.enabled:
            return []

        endpoint = os.environ.get(config.endpoint_env or "", "")
        if not endpoint:
            logger.warning(
                f"Proxy enabled but no endpoint found in env var: {config.endpoint_env}"
            )
            return []

        if config.provider == "rotating":
            # Rotating residential: same endpoint, provider handles IP rotation
            # Create N "slots" pointing to same endpoint
            # Provider uses session ID or other mechanism for stickiness
            logger.debug(
                f"Rotating proxy: {config.pool_size} slots using {self._sanitize_url(endpoint)}"
            )
            return [endpoint] * config.pool_size

        else:
            # Static: single endpoint (datacenter or residential single IP)
            logger.debug(f"Static proxy: {self._sanitize_url(endpoint)}")
            return [endpoint]

    def _sanitize_url(self, url: str) -> str:
        """
        Sanitize proxy URL for logging (hide credentials).

        Args:
            url: Proxy URL (may contain credentials)

        Returns:
            Sanitized URL safe for logging
        """
        if not url:
            return url

        # Hide credentials in URLs like http://user:pass@proxy:port
        if "@" in url:
            protocol, rest = url.split("://", 1)
            if "@" in rest:
                credentials, host = rest.rsplit("@", 1)
                return f"{protocol}://***:***@{host}"

        return url

    def get_pool_size(self) -> int:
        """
        Get current pool size.

        Returns:
            Number of proxies in pool
        """
        return len(self._pool)

    def is_enabled(self) -> bool:
        """
        Check if proxy is enabled.

        Returns:
            True if proxy is enabled and configured
        """
        return bool(self._pool)

    def get_stats(self) -> Dict[str, any]:
        """
        Get proxy rotation statistics.

        Returns:
            Dict with stats about proxy usage
        """
        return {
            "enabled": self.is_enabled(),
            "pool_size": self.get_pool_size(),
            "current_index": self._current_index,
            "provider": self.config.provider,
            "rotate_per": self.config.rotate_per,
            "total_rotations": self._current_index,
        }
