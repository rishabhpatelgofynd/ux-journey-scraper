"""
Element intelligence for finding ALL clickable elements on a page.

Uses 4-strategy detection:
1. Semantic (a, button)
2. ARIA roles
3. Event listeners (onclick, @click, ng-click)
4. CSS cursor (cursor: pointer)

Plus priority scoring and honeypot filtering.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ElementIntelligence:
    """Smart clickable element detection."""

    # Priority keyword scoring (aligned with navigation_queue.py)
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

    async def find_all_clickables(
        self,
        page,
        in_viewport_only: bool = False,
        max_elements: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Find ALL clickable elements using 4-strategy detection.

        Args:
            page: Playwright page object
            in_viewport_only: Only return elements currently in viewport
            max_elements: Maximum elements to return (performance limit)

        Returns:
            List of clickable element dictionaries, sorted by priority (high to low)
        """
        logger.debug("Finding all clickable elements...")

        try:
            clickables = await page.evaluate(
                """
                (args) => {
                    const inViewportOnly = args.inViewportOnly;
                    const maxElements = args.maxElements;
                    const clickable = [];
                    const seen = new Set();

                    // Helper: Check if element is visible
                    function isVisible(el) {
                        if (!el) return false;

                        const style = window.getComputedStyle(el);
                        if (style.display === 'none' ||
                            style.visibility === 'hidden' ||
                            style.opacity === '0') {
                            return false;
                        }

                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) {
                            return false;
                        }

                        return true;
                    }

                    // Helper: Check if element is in viewport
                    function isInViewport(el) {
                        const rect = el.getBoundingClientRect();
                        return (
                            rect.top >= 0 &&
                            rect.left >= 0 &&
                            rect.bottom <= window.innerHeight &&
                            rect.right <= window.innerWidth
                        );
                    }

                    // Helper: Check if element is honeypot (invisible but present)
                    function isHoneypot(el) {
                        const style = window.getComputedStyle(el);

                        // Common honeypot patterns
                        if (style.position === 'absolute' &&
                            (parseInt(style.left) < -9000 ||
                             parseInt(style.top) < -9000)) {
                            return true;
                        }

                        if (parseFloat(style.opacity) < 0.01) {
                            return true;
                        }

                        // Check for aria-hidden
                        if (el.getAttribute('aria-hidden') === 'true') {
                            return true;
                        }

                        return false;
                    }

                    // Strategy 1: Semantic elements
                    const semantic = document.querySelectorAll(
                        'a[href], button:not([disabled]), input[type="submit"]:not([disabled]), input[type="button"]:not([disabled])'
                    );

                    // Strategy 2: ARIA roles
                    const aria = document.querySelectorAll(
                        '[role="button"], [role="link"], [role="menuitem"], [role="tab"]'
                    );

                    // Strategy 3: Event listeners
                    const withEvents = Array.from(document.querySelectorAll('*'))
                        .filter(el =>
                            el.onclick ||
                            el.getAttribute('onclick') ||
                            el.getAttribute('@click') ||
                            el.getAttribute('ng-click') ||
                            el.getAttribute('v-on:click') ||
                            el.getAttribute('(click)')
                        );

                    // Strategy 4: Cursor pointer
                    const withCursor = Array.from(document.querySelectorAll('*'))
                        .filter(el => {
                            const style = window.getComputedStyle(el);
                            return style.cursor === 'pointer' &&
                                   el.tagName !== 'A' &&
                                   el.tagName !== 'BUTTON';
                        });

                    // Combine all strategies
                    const all = [
                        ...Array.from(semantic),
                        ...Array.from(aria),
                        ...withEvents,
                        ...withCursor
                    ];

                    // Process and deduplicate
                    for (const el of all) {
                        if (seen.has(el)) continue;
                        if (!isVisible(el)) continue;
                        if (isHoneypot(el)) continue;

                        // Viewport filter
                        const inVp = isInViewport(el);
                        if (inViewportOnly && !inVp) continue;

                        seen.add(el);

                        const rect = el.getBoundingClientRect();

                        // Extract element info
                        const text = el.innerText?.trim().slice(0, 200) || '';
                        const href = el.href || el.getAttribute('href') || '';
                        const role = el.getAttribute('role') || '';
                        const ariaLabel = el.getAttribute('aria-label') || '';

                        // Generate unique selector
                        let selector = '';
                        if (el.id) {
                            selector = '#' + el.id;
                        } else if (el.className && typeof el.className === 'string') {
                            const classes = el.className.trim().split(/\\s+/);
                            selector = el.tagName.toLowerCase() + '.' + classes.join('.');
                        } else {
                            selector = el.tagName.toLowerCase();
                        }

                        clickable.push({
                            tag: el.tagName.toLowerCase(),
                            text: text,
                            href: href,
                            role: role,
                            aria_label: ariaLabel,
                            class: el.className,
                            id: el.id,
                            selector: selector,
                            rect: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                            },
                            in_viewport: inVp,
                            // Priority will be calculated in Python
                            priority: 0,
                        });

                        // Limit for performance
                        if (clickable.length >= maxElements) {
                            break;
                        }
                    }

                    return clickable;
                }
                """,
                {"inViewportOnly": in_viewport_only, "maxElements": max_elements},
            )

            # Calculate priority for each element
            for element in clickables:
                element["priority"] = self.calculate_priority(element)

            # Sort by priority (highest first)
            clickables.sort(key=lambda x: x["priority"], reverse=True)

            logger.debug(f"Found {len(clickables)} clickable elements")
            return clickables

        except Exception as e:
            logger.error(f"Error finding clickables: {e}")
            return []

    def calculate_priority(self, element: Dict[str, Any]) -> int:
        """
        Calculate priority score for a clickable element.

        Args:
            element: Element dictionary from find_all_clickables

        Returns:
            Priority score (0-100)
        """
        # Combine text fields for keyword matching
        combined_text = " ".join(
            [
                element.get("text", ""),
                element.get("href", ""),
                element.get("aria_label", ""),
                element.get("role", ""),
            ]
        ).lower()

        # Find highest matching keyword priority
        max_priority = 0
        for keyword, priority in self.PRIORITY_KEYWORDS.items():
            if keyword in combined_text:
                max_priority = max(max_priority, priority)

        # Boost for certain element types
        tag = element.get("tag", "")
        if tag == "button":
            max_priority += 5
        elif tag == "input":
            max_priority += 5
        elif tag == "a":
            max_priority += 2

        # Boost for form submit elements
        if element.get("role") == "button" or "submit" in combined_text:
            max_priority += 5

        # Penalty for external links
        href = element.get("href", "")
        if href and href.startswith("http"):
            # External link penalty
            max_priority = max(0, max_priority - 20)

        # Penalty for mailto/tel links
        if href.startswith(("mailto:", "tel:")):
            max_priority = max(0, max_priority - 30)

        # Penalty for anchor links (same page)
        if href.startswith("#"):
            max_priority = max(0, max_priority - 40)

        # Boost for elements in viewport
        if element.get("in_viewport", False):
            max_priority += 10

        # Default priority for unmatched elements
        if max_priority == 0:
            if tag in ["button", "a", "input"]:
                max_priority = 20
            else:
                max_priority = 10

        return min(100, max_priority)  # Cap at 100

    async def get_element_center(
        self,
        page,
        selector: str,
    ) -> tuple[float, float] | None:
        """
        Get center coordinates of an element.

        Args:
            page: Playwright page
            selector: CSS selector

        Returns:
            (x, y) tuple or None if element not found
        """
        try:
            element = await page.query_selector(selector)
            if not element:
                return None

            box = await element.bounding_box()
            if not box:
                return None

            center_x = box["x"] + box["width"] / 2
            center_y = box["y"] + box["height"] / 2

            return (center_x, center_y)

        except Exception as e:
            logger.error(f"Error getting element center: {e}")
            return None

    async def filter_clickables(
        self,
        clickables: List[Dict[str, Any]],
        min_priority: int = 20,
        exclude_patterns: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter clickables by criteria.

        Args:
            clickables: List of clickable elements
            min_priority: Minimum priority to include
            exclude_patterns: List of text patterns to exclude

        Returns:
            Filtered list of clickables
        """
        if exclude_patterns is None:
            exclude_patterns = []

        filtered = []
        for el in clickables:
            # Priority filter
            if el["priority"] < min_priority:
                continue

            # Pattern exclusion
            combined_text = " ".join(
                [
                    el.get("text", ""),
                    el.get("href", ""),
                    el.get("aria_label", ""),
                ]
            ).lower()

            excluded = False
            for pattern in exclude_patterns:
                if pattern.lower() in combined_text:
                    excluded = True
                    break

            if not excluded:
                filtered.append(el)

        return filtered
