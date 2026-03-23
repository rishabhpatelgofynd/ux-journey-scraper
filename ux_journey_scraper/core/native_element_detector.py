"""
Native element detector for Appium-based mobile crawling.

Traverses the accessibility tree and priority-scores interactive elements using
the same keyword table as NavigationQueue.PRIORITY_KEYWORDS.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class NativeElement:
    """Represents a single interactive element from the native accessibility tree."""

    element_id: str
    text: str
    element_type: str    # e.g. "XCUIElementTypeButton" / "android.widget.Button"
    bounds: Dict         # {"x": 0, "y": 0, "width": 100, "height": 44}
    priority: int = 0


# XPath expressions for each platform
_ANDROID_XPATH = (
    "//android.widget.Button"
    " | //android.widget.TextView[@clickable='true']"
    " | //android.widget.ImageButton"
    " | //android.widget.LinearLayout[@clickable='true']"
    " | //android.view.View[@clickable='true']"
    " | //android.widget.RelativeLayout[@clickable='true']"
    " | //android.widget.FrameLayout[@clickable='true']"
)

_IOS_XPATH = (
    "//XCUIElementTypeButton"
    " | //XCUIElementTypeCell"
    " | //XCUIElementTypeLink"
    " | //XCUIElementTypeSwitch"
)


class NativeElementDetector:
    """
    Finds interactive elements in a native app using Appium's accessibility tree
    and scores them with the same priority keywords used by the web crawler.
    """

    # Copied verbatim from NavigationQueue.PRIORITY_KEYWORDS
    PRIORITY_KEYWORDS: Dict[str, int] = {
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

    def find_interactive(self, driver, platform_type: str) -> List[NativeElement]:
        """
        Find all interactive elements on the current screen.

        Args:
            driver: Appium WebDriver
            platform_type: "native_android" or "native_ios"

        Returns:
            List of NativeElement sorted by priority descending
        """
        if platform_type == "native_android":
            elements = self._android_elements(driver)
        else:
            elements = self._ios_elements(driver)

        for el in elements:
            el.priority = self.score(el)

        elements.sort(key=lambda e: e.priority, reverse=True)
        return elements

    def _android_elements(self, driver) -> List[NativeElement]:
        """Find interactive elements on Android via XPath."""
        results = []
        try:
            raw = driver.find_elements("xpath", _ANDROID_XPATH)
            for el in raw:
                results.append(self._to_native_element(el))
        except Exception as exc:
            logger.debug(f"Android element search error: {exc}")
        return results

    def _ios_elements(self, driver) -> List[NativeElement]:
        """Find interactive elements on iOS via XPath."""
        results = []
        try:
            raw = driver.find_elements("xpath", _IOS_XPATH)
            for el in raw:
                results.append(self._to_native_element(el))
        except Exception as exc:
            logger.debug(f"iOS element search error: {exc}")
        return results

    def _to_native_element(self, el) -> NativeElement:
        """Convert an Appium WebElement to NativeElement."""
        try:
            text = el.text or ""
        except Exception:
            text = ""

        try:
            el_type = el.get_attribute("type") or el.tag_name or ""
        except Exception:
            el_type = ""

        try:
            loc = el.location or {}
            size = el.size or {}
            bounds = {
                "x": loc.get("x", 0),
                "y": loc.get("y", 0),
                "width": size.get("width", 0),
                "height": size.get("height", 0),
            }
        except Exception:
            bounds = {"x": 0, "y": 0, "width": 0, "height": 0}

        try:
            element_id = el.id
        except Exception:
            element_id = str(id(el))

        return NativeElement(
            element_id=element_id,
            text=text,
            element_type=el_type,
            bounds=bounds,
        )

    def score(self, element: NativeElement) -> int:
        """
        Calculate priority score for a native element.

        Args:
            element: NativeElement to score

        Returns:
            Priority score (higher = more important)
        """
        text = element.text.lower()
        for keyword, score in self.PRIORITY_KEYWORDS.items():
            if keyword in text:
                return score
        return 10  # default low priority

    def is_flutter_only(self, elements: List[NativeElement], platform_type: str) -> bool:
        """
        Heuristic: if all found elements are generic view types with no text,
        the app is likely Flutter with semantics disabled.

        Args:
            elements: List of found NativeElements
            platform_type: "native_android" or "native_ios"

        Returns:
            True if elements suggest a Flutter app without semantics
        """
        if not elements:
            return True

        flutter_ios_type = "XCUIElementTypeOther"
        flutter_android_type = "android.view.View"

        for el in elements:
            if platform_type == "native_ios" and el.element_type != flutter_ios_type:
                return False
            if platform_type == "native_android" and el.element_type != flutter_android_type:
                return False
            if el.text.strip():
                return False

        return True
