"""
Three-layer state deduplication for autonomous crawling.

Prevents infinite loops in SPAs and dynamic sites by detecting:
1. URL normalization (same page, different tracking params)
2. DOM content hash (same content, different URL)
3. Structural hash (same structure, different content)
"""

import hashlib
import re
from typing import Set
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup


class StateRegistry:
    """Tracks visited states to prevent duplicate crawling."""

    # Tracking parameters to remove during URL normalization
    TRACKING_PARAMS = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_content",
        "utm_term",
        "fbclid",
        "gclid",
        "msclkid",
        "ref",
        "referrer",
        "_ga",
        "_gl",
        "mc_cid",
        "mc_eid",
    }

    # Patterns that should always be captured (exceptions to dedup)
    ALWAYS_CAPTURE_PATTERNS = [
        r"/checkout",
        r"/cart",
        r"/payment",
        r"/confirm",
        r"/thank[_-]?you",
        r"/success",
        r"/order[_-]?complete",
    ]

    def __init__(self):
        """Initialize empty state registry."""
        self.seen_urls: Set[str] = set()
        self.seen_dom_hashes: Set[str] = set()
        self.seen_structural_hashes: Set[str] = set()

    def is_new_state(self, url: str, dom_content: str) -> bool:
        """
        Check if this URL + DOM combination represents a new state.

        Args:
            url: Current page URL
            dom_content: HTML content of the page

        Returns:
            True if this is a new state (should capture), False if duplicate
        """
        # Check if URL matches always-capture patterns
        if self._should_always_capture(url):
            return True

        # Layer 1: Normalized URL check
        normalized_url = self.normalize_url(url)
        if normalized_url in self.seen_urls:
            return False

        # Layer 2: DOM content hash
        dom_hash = self._hash_dom(dom_content)
        if dom_hash in self.seen_dom_hashes:
            return False

        # Layer 3: Structural hash
        structural_hash = self._hash_structure(dom_content)
        if structural_hash in self.seen_structural_hashes:
            return False

        # New state - register it
        self.seen_urls.add(normalized_url)
        self.seen_dom_hashes.add(dom_hash)
        self.seen_structural_hashes.add(structural_hash)

        return True

    def mark_visited(self, url: str, dom_content: str) -> None:
        """
        Explicitly mark a state as visited.

        Useful for marking states that were captured but may not have
        gone through is_new_state() check.

        Args:
            url: Page URL
            dom_content: HTML content
        """
        normalized_url = self.normalize_url(url)
        dom_hash = self._hash_dom(dom_content)
        structural_hash = self._hash_structure(dom_content)

        self.seen_urls.add(normalized_url)
        self.seen_dom_hashes.add(dom_hash)
        self.seen_structural_hashes.add(structural_hash)

    def normalize_url(self, url: str) -> str:
        """
        Normalize URL by removing tracking parameters and fragments.

        Args:
            url: Raw URL

        Returns:
            Normalized URL string
        """
        parsed = urlparse(url)

        # Remove tracking query parameters
        params = parse_qs(parsed.query)
        clean_params = {
            k: v for k, v in params.items() if k not in self.TRACKING_PARAMS
        }

        # Sort params for consistent ordering
        sorted_params = sorted(clean_params.items())
        clean_query = urlencode(sorted_params, doseq=True)

        # Rebuild URL without fragment and with clean params
        normalized = urlunparse(
            (
                parsed.scheme,
                parsed.netloc.lower(),  # Lowercase domain
                parsed.path.rstrip("/") or "/",  # Remove trailing slash, keep root
                parsed.params,
                clean_query,
                "",  # Remove fragment (#section)
            )
        )

        return normalized

    def _hash_dom(self, dom_content: str) -> str:
        """
        Hash the full DOM content.

        Layer 2: Detects identical content at different URLs.

        Args:
            dom_content: HTML string

        Returns:
            MD5 hash of DOM content
        """
        # Hash the full content
        return hashlib.md5(dom_content.encode("utf-8", errors="ignore")).hexdigest()

    def _hash_structure(self, dom_content: str) -> str:
        """
        Hash the DOM structure (tags only, no content).

        Layer 3: Detects same layout with different content
        (e.g., product pages with different products).

        Args:
            dom_content: HTML string

        Returns:
            MD5 hash of DOM structure
        """
        try:
            soup = BeautifulSoup(dom_content, "html.parser")

            # Extract structural signature
            signature = self._extract_structural_signature(soup)

            return hashlib.md5(signature.encode("utf-8")).hexdigest()
        except Exception:
            # If parsing fails, fall back to full content hash
            return self._hash_dom(dom_content)

    def _extract_structural_signature(self, soup: BeautifulSoup) -> str:
        """
        Extract a structural signature from DOM (tags + classes, no content).

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Structural signature string
        """
        # Build signature from tag names and key attributes
        parts = []

        for tag in soup.find_all(True):  # All tags
            # Include tag name
            tag_sig = tag.name

            # Include classes (important for structure)
            if tag.get("class"):
                classes = " ".join(sorted(tag.get("class")))
                tag_sig += f".{classes}"

            # Include IDs
            if tag.get("id"):
                tag_sig += f"#{tag.get('id')}"

            # Include certain structural attributes
            if tag.name == "img" and tag.get("alt"):
                tag_sig += f"[alt]"
            if tag.name in ["input", "button"] and tag.get("type"):
                tag_sig += f"[type={tag.get('type')}]"

            parts.append(tag_sig)

            # Limit signature length for performance
            if len(parts) > 500:
                break

        return " ".join(parts)

    def _should_always_capture(self, url: str) -> bool:
        """
        Check if URL matches always-capture patterns.

        Certain flows (checkout, payment) should always be captured
        even if they look similar structurally.

        Args:
            url: URL to check

        Returns:
            True if this URL should always be captured
        """
        for pattern in self.ALWAYS_CAPTURE_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def reset(self) -> None:
        """Clear all registered states."""
        self.seen_urls.clear()
        self.seen_dom_hashes.clear()
        self.seen_structural_hashes.clear()

    def get_stats(self) -> dict:
        """
        Get statistics about registered states.

        Returns:
            Dictionary with state counts
        """
        return {
            "unique_urls": len(self.seen_urls),
            "unique_dom_hashes": len(self.seen_dom_hashes),
            "unique_structures": len(self.seen_structural_hashes),
            "total_states": max(
                len(self.seen_urls),
                len(self.seen_dom_hashes),
                len(self.seen_structural_hashes),
            ),
        }
