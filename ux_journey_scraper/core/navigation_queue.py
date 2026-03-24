"""
Priority queue-based navigation engine for autonomous crawling.

Uses a max-heap to prioritize high-value actions (e.g., "Add to Cart" before "Learn More").
Integrates with StateRegistry to avoid duplicate states.
"""

import heapq
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class NavigationAction:
    """Represents a potential navigation action."""

    type: str  # "navigate", "click", "fill_form", "scroll"
    priority: int  # Higher = more important
    depth: int  # Distance from seed URL (for max_depth limiting)
    url: str  # Current or target URL
    selector: Optional[str] = None  # CSS selector for click/fill actions
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extra context

    def __lt__(self, other):
        """Comparison for heap (higher priority first, then lower depth)."""
        if self.priority != other.priority:
            return self.priority > other.priority  # Max-heap by priority
        return self.depth < other.depth  # Then by depth (prefer shallower)

    def __repr__(self):
        """String representation for debugging."""
        return (
            f"NavigationAction(type={self.type}, priority={self.priority}, "
            f"depth={self.depth}, url={self.url[:50]}...)"
        )


class NavigationQueue:
    """Priority queue for autonomous crawling decisions."""

    # Priority scores for common UI elements (from Perfect Scraping spec)
    PRIORITY_KEYWORDS = {
        # Checkout flow (highest priority)
        "add to cart": 100,
        "add to bag": 100,
        "buy now": 95,
        "checkout": 90,
        "place order": 90,
        "complete order": 90,
        "confirm payment": 90,
        # Flow progression
        "continue": 80,
        "next": 75,
        "proceed": 75,
        "submit": 70,
        # Navigation
        "shop": 60,
        "products": 60,
        "categories": 55,
        "menu": 50,
        # Secondary actions
        "view details": 40,
        "learn more": 35,
        "read more": 35,
        "about": 30,
        "contact": 25,
        # Low priority
        "privacy": 10,
        "terms": 10,
        "cookie policy": 5,
        "unsubscribe": 5,
    }

    def __init__(self, max_depth: int = 8):
        """
        Initialize navigation queue.

        Args:
            max_depth: Maximum depth to crawl from seed URLs
        """
        self.queue: List[NavigationAction] = []  # Min-heap (we negate priorities)
        self.queued_actions: Set[str] = set()  # Dedup by action signature
        self.max_depth = max_depth
        self.actions_processed = 0

    def add(self, action: NavigationAction) -> bool:
        """
        Add action to queue if not duplicate and within depth limit.

        Args:
            action: NavigationAction to add

        Returns:
            True if added, False if duplicate or rejected
        """
        # Check depth limit
        if action.depth > self.max_depth:
            return False

        # Check for duplicate action
        action_sig = self._action_signature(action)
        if action_sig in self.queued_actions:
            return False

        # Add to queue
        heapq.heappush(self.queue, action)
        self.queued_actions.add(action_sig)
        return True

    def add_batch(self, actions: List[NavigationAction]) -> int:
        """
        Add multiple actions at once.

        Args:
            actions: List of NavigationActions

        Returns:
            Number of actions successfully added
        """
        added = 0
        for action in actions:
            if self.add(action):
                added += 1
        return added

    def next(self) -> Optional[NavigationAction]:
        """
        Get next highest-priority action.

        Returns:
            NavigationAction or None if queue is empty
        """
        if not self.queue:
            return None

        action = heapq.heappop(self.queue)
        self.actions_processed += 1
        return action

    def peek(self) -> Optional[NavigationAction]:
        """
        Look at next action without removing it.

        Returns:
            NavigationAction or None if queue is empty
        """
        return self.queue[0] if self.queue else None

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self.queue) == 0

    def size(self) -> int:
        """Get number of actions in queue."""
        return len(self.queue)

    def calculate_priority(
        self,
        element_text: str = "",
        element_type: str = "",
        href: str = "",
        aria_label: str = "",
    ) -> int:
        """
        Calculate priority score for an element.

        Args:
            element_text: Visible text of element
            element_type: Tag name or role (button, link, etc.)
            href: href attribute if link
            aria_label: aria-label attribute

        Returns:
            Priority score (0-100)
        """
        # Combine all text fields for keyword matching
        combined_text = " ".join([element_text, element_type, href, aria_label]).lower()

        # Check for keyword matches
        max_priority = 0
        for keyword, priority in self.PRIORITY_KEYWORDS.items():
            if keyword in combined_text:
                max_priority = max(max_priority, priority)

        # Boost priority for certain element types
        if element_type in ["button", "submit"]:
            max_priority += 5
        elif element_type == "link":
            max_priority += 2

        # Penalty for external links (if href provided)
        if href and self._is_external_link(href):
            max_priority = max(0, max_priority - 30)

        # Default priority for elements with no keywords
        if max_priority == 0:
            if element_type in ["button", "link"]:
                max_priority = 20  # Base priority for interactive elements
            else:
                max_priority = 10

        return min(100, max_priority)  # Cap at 100

    def _action_signature(self, action: NavigationAction) -> str:
        """
        Generate unique signature for action deduplication.

        Args:
            action: NavigationAction

        Returns:
            Signature string
        """
        if action.type == "navigate":
            return f"nav:{action.url}"
        elif action.type == "click":
            return f"click:{action.url}:{action.selector}"
        elif action.type == "fill_form":
            return f"form:{action.url}:{action.selector}"
        else:
            return f"{action.type}:{action.url}:{action.selector}"

    def _is_external_link(self, href: str) -> bool:
        """
        Check if href is external link.

        Args:
            href: URL or path

        Returns:
            True if external (starts with http and different domain)
        """
        if not href:
            return False

        # Relative paths are internal
        if not href.startswith("http"):
            return False

        # Same domain check would require base_url context
        # For now, treat all absolute http:// links as potentially external
        return True

    def clear_low_priority(self, threshold: int = 20) -> int:
        """
        Remove all actions below a priority threshold.

        Useful for focusing on high-value actions when queue gets too large.

        Args:
            threshold: Minimum priority to keep

        Returns:
            Number of actions removed
        """
        original_size = len(self.queue)

        # Filter queue
        self.queue = [action for action in self.queue if action.priority >= threshold]
        heapq.heapify(self.queue)

        # Rebuild queued_actions set
        self.queued_actions = {self._action_signature(action) for action in self.queue}

        removed = original_size - len(self.queue)
        return removed

    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dictionary with queue stats
        """
        if not self.queue:
            return {
                "queue_size": 0,
                "actions_processed": self.actions_processed,
                "max_depth": self.max_depth,
            }

        priorities = [action.priority for action in self.queue]
        depths = [action.depth for action in self.queue]

        return {
            "queue_size": len(self.queue),
            "actions_processed": self.actions_processed,
            "max_depth": self.max_depth,
            "avg_priority": sum(priorities) / len(priorities),
            "max_priority": max(priorities),
            "min_priority": min(priorities),
            "avg_depth": sum(depths) / len(depths),
            "max_depth_in_queue": max(depths),
        }

    def reset(self) -> None:
        """Clear queue and reset counters."""
        self.queue.clear()
        self.queued_actions.clear()
        self.actions_processed = 0
