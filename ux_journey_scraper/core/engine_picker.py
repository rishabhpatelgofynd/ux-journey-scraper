"""
Engine selection and AI-powered navigation stubs.

These are future capabilities documented as stubs for the scraper roadmap:

- EnginePicker: Select the lightest capture engine for a given URL
  (e.g., static fetch for simple pages, full browser for SPAs).
- AINavigator: Use an LLM to decide which elements to interact with
  during autonomous crawling (Task 4.2 / 4.4).

Both classes are intentionally minimal. They define the public API
surface so that callers can integrate early, but raise
``NotImplementedError`` for any logic that requires future work.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class EnginePicker:
    """Select the lightest scraping engine suitable for a URL.

    Future engine tiers (lightest to heaviest):

    1. **static** -- plain HTTP fetch + HTML parse. Fastest, no JS.
    2. **light** -- headless browser with JS disabled, only DOM capture.
    3. **browser** -- full Playwright/Puppeteer with JS execution.
    4. **authenticated** -- browser + login/session management.

    Selection criteria (planned):
    - robots.txt / meta tags indicating static content
    - Presence of JS framework markers (React, Vue, Angular)
    - Whether authentication is required
    - Historical success rate per engine for the domain

    Currently always returns ``"browser"`` as the safe default.
    """

    # Maps engine names to a rough cost weight (1 = cheapest)
    ENGINE_COSTS: Dict[str, int] = {
        "static": 1,
        "light": 2,
        "browser": 5,
        "authenticated": 8,
    }

    def pick(self, url: str, hints: Optional[Dict[str, Any]] = None) -> str:
        """Choose the best engine for *url*.

        Args:
            url: The target URL to scrape.
            hints: Optional dict with pre-known info about the page
                   (e.g., ``{"framework": "react", "auth_required": True}``).

        Returns:
            Engine name string. Currently always ``"browser"``.
        """
        # TODO: Implement lightweight pre-flight check (HEAD request,
        #       robots.txt parse, domain history lookup) to choose a
        #       cheaper engine when possible.
        logger.debug("EnginePicker: defaulting to 'browser' for %s", url)
        return "browser"

    def cost(self, engine: str) -> int:
        """Return the relative cost weight of *engine*.

        Args:
            engine: Engine name (e.g., ``"static"``, ``"browser"``).

        Returns:
            Integer cost weight.

        Raises:
            ValueError: If *engine* is not a known engine name.
        """
        if engine not in self.ENGINE_COSTS:
            raise ValueError(
                f"Unknown engine '{engine}'. "
                f"Known engines: {list(self.ENGINE_COSTS)}"
            )
        return self.ENGINE_COSTS[engine]


class AINavigator:
    """AI-powered navigation decision maker (stub).

    Future capability: use an LLM to examine the current page state
    (DOM snapshot, screenshot, journey context) and decide which
    element to interact with next during autonomous crawling.

    This replaces keyword-based priority heuristics with contextual
    understanding -- e.g., recognising that a "Size" dropdown must be
    selected before "Add to Cart" becomes clickable.

    All methods raise ``NotImplementedError`` until the integration is
    built.
    """

    def __init__(self, model: str = "default") -> None:
        """Initialize the AI navigator.

        Args:
            model: LLM model identifier to use for decisions.
        """
        self.model = model

    async def decide_next_action(
        self,
        page_snapshot: Dict[str, Any],
        journey_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Decide the next navigation action given current page state.

        Args:
            page_snapshot: Dictionary with keys like ``html``,
                ``screenshot_path``, ``url``, ``interactive_elements``.
            journey_context: Optional context about the journey so far
                (pages visited, goal, etc.).

        Returns:
            Action dictionary with ``type``, ``selector``, ``reason``.

        Raises:
            NotImplementedError: Always -- this is a future capability.
        """
        raise NotImplementedError(
            "AINavigator.decide_next_action is a planned future capability. "
            "See docs/superpowers/specs/ for the design."
        )

    async def evaluate_page_importance(
        self,
        page_snapshot: Dict[str, Any],
    ) -> float:
        """Score how important the current page is to the journey goal.

        Args:
            page_snapshot: Dictionary describing the current page.

        Returns:
            Float between 0.0 (irrelevant) and 1.0 (critical).

        Raises:
            NotImplementedError: Always -- this is a future capability.
        """
        raise NotImplementedError(
            "AINavigator.evaluate_page_importance is a planned future capability. "
            "See docs/superpowers/specs/ for the design."
        )
