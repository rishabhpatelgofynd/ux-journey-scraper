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
        Initialize proxy rotator with tiered escalation support.

        Tracks errors per domain per tier and auto-escalates to
        stealthier proxies when blocking is detected.

        Tiers:
          0 = Direct (no proxy)
          1 = Datacenter proxy
          2 = Residential/stealth proxy

        Args:
            config: Proxy settings from scrape config
        """
        self.config = config
        self._pool = self._build_pool(config)
        self._current_index = 0

        # Tiered proxy escalation: domain -> {tier -> error_count}
        self._error_counts: Dict[str, Dict[int, int]] = {}
        # Tier endpoint env vars (configurable via config.tiers if present)
        self._tier_endpoints: Dict[int, str] = {
            0: "",  # Direct
            1: os.environ.get("PROXY_DATACENTER_URL", ""),
            2: os.environ.get("PROXY_RESIDENTIAL_URL", ""),
        }

        if self._pool:
            logger.info(
                f"ProxyRotator initialized: {len(self._pool)} endpoints, "
                f"provider={config.provider}"
            )
        else:
            logger.info("ProxyRotator: proxy disabled")

    def report_error(self, domain: str, tier: int = 0) -> None:
        """Report a blocked/failed request for a domain at a given tier."""
        if domain not in self._error_counts:
            self._error_counts[domain] = {}
        self._error_counts[domain][tier] = self._error_counts[domain].get(tier, 0) + 10
        logger.debug(f"Proxy error for {domain} at tier {tier}: count={self._error_counts[domain][tier]}")

    def report_success(self, domain: str, tier: int = 0) -> None:
        """Report a successful request for a domain at a given tier."""
        if domain not in self._error_counts:
            return
        if tier in self._error_counts[domain]:
            self._error_counts[domain][tier] = max(0, self._error_counts[domain][tier] - 1)

    def get_recommended_tier(self, domain: str) -> int:
        """Get the recommended proxy tier for a domain based on error history.

        Returns the lowest tier with the fewest errors. Escalates to higher
        tiers when lower tiers are consistently blocked.
        """
        if domain not in self._error_counts:
            return 0  # Start with direct

        errors = self._error_counts[domain]
        # Find tier with lowest error count
        best_tier = 0
        best_errors = errors.get(0, 0)
        for tier in [1, 2]:
            tier_errors = errors.get(tier, 0)
            if tier_errors < best_errors:
                best_tier = tier
                best_errors = tier_errors

        # Only escalate if current tier has significant errors
        if errors.get(0, 0) >= 30:  # 3+ blocks at direct
            if errors.get(1, 0) >= 30:  # 3+ blocks at datacenter
                return 2  # Escalate to residential
            return max(best_tier, 1)  # At least datacenter

        return best_tier

    def get_proxy_for_tier(self, tier: int) -> Optional[Dict[str, str]]:
        """Get proxy config for a specific tier.

        Returns None for tier 0 (direct) or if tier endpoint not configured.
        """
        if tier == 0:
            return None
        endpoint = self._tier_endpoints.get(tier, "")
        if not endpoint:
            return None
        return {"server": endpoint}

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
