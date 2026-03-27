"""Smart page selection for full page type coverage with limits."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from ux_journey_scraper.core.anti_crawler_detector import AntiCrawlerDetector
from ux_journey_scraper.core.page_classifier import PageClassifier


class PageSelector:
    """Selects pages to capture ensuring complete page type coverage."""

    TYPE_PRIORITY: dict[str, int] = {
        "homepage": 100,
        "cart": 90,
        "checkout": 85,
        "plp": 80,
        "pdp": 70,
        "search": 65,
        "account": 60,
        "policy": 50,
        "info": 45,
        "content": 40,
        "other": 20,
    }

    TYPE_LIMITS: dict[str, int] = {
        "homepage": 1,
        "plp": 5,
        "pdp": 10,
        "cart": 1,
        "checkout": 5,
        "account": 3,
        "search": 2,
        "policy": 99,
        "info": 99,
        "content": 3,
        "other": 5,
    }

    @classmethod
    def select(
        cls, urls: list[str], base_domain: str
    ) -> list[dict[str, Any]]:
        """Select pages to capture with full type coverage and limits.

        Filters pagination, classifies each URL, groups by type,
        selects within limits, and sorts by priority.

        Args:
            urls: List of discovered URLs.
            base_domain: The base domain being crawled.

        Returns:
            List of dicts with 'url', 'page_type', and 'priority' keys,
            sorted by priority descending.
        """
        # Step 1: Filter pagination URLs
        filtered_urls = AntiCrawlerDetector.limit_pagination(urls)

        # Step 2: Classify each URL
        classified: list[dict[str, Any]] = []
        for url in filtered_urls:
            page_type = PageClassifier.classify_url(url)
            classified.append({
                "url": url,
                "page_type": page_type,
                "priority": cls.TYPE_PRIORITY.get(page_type, 20),
            })

        # Step 3: Group by type
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in classified:
            groups[item["page_type"]].append(item)

        # Step 4: Select within limits
        selected: list[dict[str, Any]] = []
        for page_type, items in groups.items():
            limit = cls.TYPE_LIMITS.get(page_type, 5)
            selected.extend(items[:limit])

        # Step 5: Sort by priority descending
        selected.sort(key=lambda x: x["priority"], reverse=True)

        return selected
