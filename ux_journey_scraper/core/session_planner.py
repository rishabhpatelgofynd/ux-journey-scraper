"""
Session planner for split-session crawls.

Plans all visit sessions before the crawl starts. Each visit session has a goal,
a page budget, an entry point, and a platform/auth assignment.
"""

import logging
import random
from dataclasses import dataclass, field
from typing import List, Optional

from ..config.scrape_config import PlatformConfig, ScrapeConfig

logger = logging.getLogger(__name__)


@dataclass
class VisitPlan:
    """Plan for a single visit session."""

    session_id: str
    goal: str  # "browse" | "search" | "cart" | "checkout" | "post_order" | "fill_gaps"
    entry_url: str  # Where this session starts
    entry_strategy: (
        str  # "homepage" | "deep_link_pdp" | "deep_link_category" | "saved_cart"
    )
    target_page_types: List[str]  # Page types to prioritize in nav queue
    max_pages: int  # Page budget for this session
    auth_state: str  # "logged_out" | "logged_in"
    platform: PlatformConfig  # Which platform config to use
    proxy_slot: int  # Which proxy IP slot to use (for rotation)


class SessionPlanner:
    """
    Generates an ordered list of VisitPlans that cover all
    platform × auth × journey combinations.

    Rules:
    - Browse sessions go first (build cookie history, look natural)
    - Cart/checkout sessions come later (real users browse before buying)
    - Post-order is last (requires logged_in state with order history)
    - Each session has a clear goal and page budget
    - Platforms alternate where possible (desktop → mobile → desktop)
    - Never schedule two logged_in sessions back-to-back on different platforms
      (same user wouldn't be on desktop AND mobile simultaneously)
    """

    # Ordered goals — browse before transact, transact before post-order
    GOAL_SEQUENCE = [
        ("browse", "logged_out", 20),
        ("search", "logged_out", 15),
        ("browse", "logged_out", 15),  # Second browse pass for depth
        ("cart", "logged_out", 12),  # Add to cart, explore cart page
        ("checkout", "logged_in", 10),  # Login → checkout → confirmation
        ("post_order", "logged_in", 8),  # Orders, tracking, returns
        ("fill_gaps", "logged_out", 15),  # Catch anything missed
    ]

    ENTRY_STRATEGIES = [
        "homepage",
        "deep_link_pdp",
        "deep_link_category",
    ]

    def plan(self, config: ScrapeConfig) -> List[VisitPlan]:
        """
        Generate visit plans for all platform × goal combinations.

        Args:
            config: Full scrape configuration

        Returns:
            Ordered list of VisitPlans ready for execution
        """
        plans = []
        proxy_slot = 0

        for platform in config.platforms:
            for i, (goal, auth, max_pages) in enumerate(self.GOAL_SEQUENCE):
                # Skip logged_in goals if auth.logged_in is False
                if auth == "logged_in" and not config.auth.logged_in:
                    logger.debug(f"Skipping {goal} (logged_in required but disabled)")
                    continue

                # Skip post_order if no seeds configured
                if goal == "post_order" and not config.post_order.get("seeds"):
                    logger.debug(f"Skipping {goal} (no post_order seeds)")
                    continue

                # Respect per-session page budget from config
                effective_pages = min(
                    max_pages, config.session_strategy.pages_per_session
                )

                # Entry point selection
                entry_url, entry_strategy = self._pick_entry(
                    config, goal, config.session_strategy.randomize_entry_points
                )

                # Proxy slot rotation
                if config.session_strategy.rotate_ip_per_session:
                    proxy_slot += 1
                elif (
                    i > 0 and i % config.session_strategy.rotate_ip_per_n_sessions == 0
                ):
                    proxy_slot += 1

                session_id = f"visit_{platform.type}_{goal}_{i:02d}"

                plans.append(
                    VisitPlan(
                        session_id=session_id,
                        goal=goal,
                        entry_url=entry_url,
                        entry_strategy=entry_strategy,
                        target_page_types=self._target_types_for_goal(goal),
                        max_pages=effective_pages,
                        auth_state=auth,
                        platform=platform,
                        proxy_slot=proxy_slot % max(config.proxy.pool_size, 1),
                    )
                )

                logger.debug(
                    f"Planned {session_id}: {goal}/{auth} on {platform.type}, "
                    f"{effective_pages} pages, entry={entry_strategy}"
                )

        logger.info(f"Session planner created {len(plans)} visit sessions")
        return plans

    def _pick_entry(self, config: ScrapeConfig, goal: str, randomize: bool) -> tuple:
        """
        Return (entry_url, entry_strategy) based on goal.

        Args:
            config: Scrape config
            goal: Session goal
            randomize: Whether to randomize entry points

        Returns:
            Tuple of (entry_url, entry_strategy)
        """
        base = config.base_url

        # Special cases for specific goals
        if goal == "checkout" and config.auth.login_url:
            return config.auth.login_url, "login_page"

        if goal == "post_order" and config.post_order.get("seeds"):
            seed = config.post_order["seeds"][0]
            url = seed.get("url", base)
            # Replace order_id placeholder if present
            if "{order_id}" in url:
                url = url.replace("{order_id}", seed.get("order_id", ""))
            return url, "deep_link_order"

        # Default to homepage for browse and fill_gaps
        if not randomize or goal in ("browse", "fill_gaps"):
            return base, "homepage"

        # Use seed_urls for deep links if available
        if config.seed_urls and goal in ("search", "cart"):
            url = random.choice(config.seed_urls)
            return url, "deep_link_pdp"

        return base, "homepage"

    def _target_types_for_goal(self, goal: str) -> List[str]:
        """
        Page types to prioritize in the nav queue for this goal.

        Args:
            goal: Session goal

        Returns:
            List of page type strings to prioritize
        """
        return {
            "browse": ["home", "plp", "pdp"],
            "search": ["search", "plp", "pdp"],
            "cart": ["pdp", "cart"],
            "checkout": ["cart", "checkout", "confirmation"],
            "post_order": ["orders", "order_detail", "tracking", "returns"],
            "fill_gaps": ["account", "wishlist", "unknown"],
        }.get(goal, [])

    def estimate_total_pages(self, plans: List[VisitPlan]) -> int:
        """
        Estimate total pages that will be captured across all sessions.

        Args:
            plans: List of visit plans

        Returns:
            Estimated total page count
        """
        return sum(plan.max_pages for plan in plans)

    def estimate_total_time(self, plans: List[VisitPlan], config: ScrapeConfig) -> int:
        """
        Estimate total crawl time in seconds.

        Args:
            plans: List of visit plans
            config: Scrape config with session strategy

        Returns:
            Estimated time in seconds
        """
        # Time per page (avg delay + page load)
        time_per_page = (
            config.crawler.delay_ms + config.crawler.timeout_per_page_ms
        ) / 1000

        # Time for all pages
        crawl_time = self.estimate_total_pages(plans) * time_per_page

        # Cooldown time between sessions
        avg_cooldown = (
            config.session_strategy.min_cooldown_sec
            + config.session_strategy.max_cooldown_sec
        ) / 2
        cooldown_time = avg_cooldown * (len(plans) - 1)

        return int(crawl_time + cooldown_time)

    def get_goals_for_auth_state(self, auth_state: str) -> List[str]:
        """
        Get all goal types for a given auth state.

        Args:
            auth_state: "logged_in" or "logged_out"

        Returns:
            List of goal strings
        """
        return [goal for goal, auth, _ in self.GOAL_SEQUENCE if auth == auth_state]
