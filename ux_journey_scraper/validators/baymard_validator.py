"""
Baymard UX validator for web pages.

Validates crawled pages against Baymard Institute UX guidelines.
"""
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

from .guideline_index import GuidelineIndex


class BaymardValidator:
    """Validate pages against Baymard UX guidelines."""

    def __init__(self, guideline_index: GuidelineIndex):
        """
        Initialize validator with guideline index.

        Args:
            guideline_index: Initialized GuidelineIndex instance
        """
        self.index = guideline_index
        self.validation_rules = self._initialize_validation_rules()

    def _initialize_validation_rules(self) -> Dict:
        """
        Initialize validation rules for specific guidelines.

        This creates a mapping of guideline IDs to validation functions.
        Each rule checks specific aspects of the page.
        """
        return {
            # Homepage guidelines
            "237": self._validate_product_range_display,
            "240": self._validate_ad_presence,
            "242": self._validate_carousel_controls,
            "957": self._validate_mobile_carousel,
            "238": self._validate_bespoke_imagery,

            # Navigation guidelines
            "300": self._validate_current_scope_highlight,
            "266": self._validate_clickable_headings,

            # Search guidelines
            # Add more as needed
        }

    def detect_page_type(self, url: str, html: str, title: str = "") -> str:
        """
        Detect page type from URL, HTML, and title.

        Args:
            url: Page URL
            html: Page HTML content
            title: Page title (optional)

        Returns:
            Detected page type
        """
        url_lower = url.lower()
        html_lower = html.lower()
        title_lower = title.lower()

        # Cart detection
        if any(pattern in url_lower for pattern in ['/cart', '/basket', 'shopping-cart']):
            return 'cart'

        # Checkout detection
        if any(pattern in url_lower for pattern in ['/checkout', '/payment', '/order']):
            return 'checkout'

        # Product page detection
        if any(pattern in url_lower for pattern in ['/product/', '/p/', '/item/', '/sku/']):
            return 'product'
        if 'product' in html_lower and 'add to cart' in html_lower:
            return 'product'

        # Search results detection
        if any(pattern in url_lower for pattern in ['/search', '?q=', '?search=']):
            return 'search'

        # Category/listing detection
        if any(pattern in url_lower for pattern in ['/category', '/collection', '/shop']):
            return 'category'

        # Homepage detection (must be after other checks)
        path_count = url_lower.rstrip('/').count('/')
        if path_count <= 2 or '/index' in url_lower or url_lower.endswith('/'):
            if 'homepage' in title_lower or path_count <= 2:
                return 'homepage'

        # Default to navigation/taxonomy
        return 'navigation'

    def validate_page(
        self,
        url: str,
        html: str,
        title: str = "",
        screenshot_path: Optional[str] = None,
        page_data: Optional[Dict] = None
    ) -> Dict:
        """
        Validate a page against relevant Baymard guidelines.

        Args:
            url: Page URL
            html: Page HTML content
            title: Page title
            screenshot_path: Optional path to screenshot
            page_data: Optional additional page data from PageAnalyzer

        Returns:
            Validation results dictionary
        """
        # Detect page type
        page_type = self.detect_page_type(url, html, title)

        # Get relevant guidelines for this page type
        relevant_guidelines = self.index.get_guidelines_for_page_type(page_type)

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # Run validations
        results = {
            "page_url": url,
            "page_type": page_type,
            "page_title": title,
            "total_guidelines_checked": len(relevant_guidelines),
            "violations": [],
            "warnings": [],
            "passed": [],
            "not_applicable": [],
            "metadata": {
                "guideline_count": len(relevant_guidelines),
                "screenshot_available": screenshot_path is not None,
            }
        }

        for guideline in relevant_guidelines:
            gid = guideline["id"]
            validation_result = self._validate_guideline(
                guideline, soup, html, url, page_data
            )

            # Categorize result
            status = validation_result.get("status", "pass")

            if status == "fail":
                results["violations"].append({
                    "guideline_id": gid,
                    "title": guideline["title"],
                    "severity": validation_result.get("severity", "medium"),
                    "details": validation_result.get("details", ""),
                    "evidence": validation_result.get("evidence", ""),
                    "recommendation": validation_result.get("recommendation", ""),
                    "reference_url": guideline.get("url", ""),
                })
            elif status == "warning":
                results["warnings"].append({
                    "guideline_id": gid,
                    "title": guideline["title"],
                    "details": validation_result.get("details", ""),
                    "reference_url": guideline.get("url", ""),
                })
            elif status == "not_applicable":
                results["not_applicable"].append(gid)
            else:  # pass
                results["passed"].append(gid)

        # Calculate compliance score
        total_applicable = len(relevant_guidelines) - len(results["not_applicable"])
        if total_applicable > 0:
            passed_count = len(results["passed"])
            results["compliance_score"] = round((passed_count / total_applicable) * 100, 1)
        else:
            results["compliance_score"] = 100.0

        # Add summary
        results["summary"] = {
            "total_checked": len(relevant_guidelines),
            "passed": len(results["passed"]),
            "violations": len(results["violations"]),
            "warnings": len(results["warnings"]),
            "not_applicable": len(results["not_applicable"]),
        }

        return results

    def _validate_guideline(
        self,
        guideline: Dict,
        soup: BeautifulSoup,
        html: str,
        url: str,
        page_data: Optional[Dict]
    ) -> Dict:
        """
        Validate a specific guideline.

        Args:
            guideline: Guideline dictionary
            soup: BeautifulSoup parsed HTML
            html: Raw HTML string
            url: Page URL
            page_data: Additional page data

        Returns:
            Validation result
        """
        gid = guideline["id"]

        # If we have a specific validation rule, use it
        if gid in self.validation_rules:
            return self.validation_rules[gid](guideline, soup, html, url, page_data)

        # Otherwise, return not_applicable (needs manual review or specific implementation)
        return {"status": "not_applicable"}

    # ========================================================================
    # Specific Validation Rules
    # ========================================================================

    def _validate_product_range_display(
        self, guideline, soup, html, url, page_data
    ) -> Dict:
        """
        Guideline #237: Feature a Broad Range of Product Types on the Homepage.

        Checks if homepage displays diverse product categories/types.
        """
        # Look for navigation with categories
        nav_elements = soup.find_all(['nav', 'header'])
        category_links = []

        for nav in nav_elements:
            # Find links that look like category links
            links = nav.find_all('a')
            for link in links:
                text = link.get_text(strip=True).lower()
                # Filter out common non-category links
                if text and text not in ['home', 'cart', 'checkout', 'login', 'account']:
                    if len(text) < 50:  # Category names are usually short
                        category_links.append(text)

        # Check for product displays
        product_indicators = [
            'product', 'item', 'shop', 'category', 'collection',
            'new arrivals', 'best seller', 'trending'
        ]

        html_lower = html.lower()
        product_variety_score = sum(
            1 for indicator in product_indicators
            if indicator in html_lower
        )

        # Validation logic
        if len(category_links) < 3 and product_variety_score < 2:
            return {
                "status": "fail",
                "severity": "high",
                "details": "Homepage lacks clear indication of product range diversity",
                "evidence": f"Found only {len(category_links)} category links and {product_variety_score} product variety indicators",
                "recommendation": "Add clear navigation menu with main product categories and/or featured product sections showcasing range"
            }
        elif len(category_links) < 5 or product_variety_score < 3:
            return {
                "status": "warning",
                "details": "Limited product range visibility on homepage",
            }

        return {"status": "pass"}

    def _validate_ad_presence(
        self, guideline, soup, html, url, page_data
    ) -> Dict:
        """
        Guideline #240: Be Cautious if Displaying Ads on the Homepage.

        Checks for advertisements that might distract users.
        """
        ad_indicators = [
            'advertisement', 'ad-banner', 'google_ads', 'adsense',
            'sponsored', 'promo-banner', 'ad-container', 'ad-slot'
        ]

        html_lower = html.lower()

        # Check for ad-related classes/ids
        ad_elements = []
        for element in soup.find_all(['div', 'iframe', 'ins']):
            class_str = ' '.join(element.get('class', [])).lower()
            id_str = element.get('id', '').lower()

            if any(indicator in class_str or indicator in id_str for indicator in ad_indicators):
                ad_elements.append(element)

        # Check for inline ad indicators
        ad_text_count = sum(1 for indicator in ad_indicators if indicator in html_lower)

        if len(ad_elements) > 2 or ad_text_count > 3:
            return {
                "status": "warning",
                "details": f"Page contains {len(ad_elements)} potential advertisement elements",
                "recommendation": "Consider reducing ad presence or ensuring ads don't dominate the homepage"
            }

        return {"status": "pass"}

    def _validate_carousel_controls(
        self, guideline, soup, html, url, page_data
    ) -> Dict:
        """
        Guideline #242: Ensure Carousels Have Appropriate Controls.

        Checks if carousels have visible navigation controls.
        """
        # Find carousel elements
        carousel_indicators = ['carousel', 'slider', 'slideshow', 'swiper']
        carousel_elements = []

        for element in soup.find_all(['div', 'section']):
            class_str = ' '.join(element.get('class', [])).lower()
            if any(indicator in class_str for indicator in carousel_indicators):
                carousel_elements.append(element)

        if not carousel_elements:
            return {"status": "not_applicable"}

        # Check for controls in carousel elements
        missing_controls = []
        for carousel in carousel_elements:
            # Look for common control elements
            has_prev_next = carousel.find_all(['button', 'a'], class_=re.compile(r'(prev|next|arrow)', re.I))
            has_dots = carousel.find_all(class_=re.compile(r'(dot|indicator|pagination)', re.I))

            if not has_prev_next and not has_dots:
                missing_controls.append(carousel)

        if len(missing_controls) > 0:
            return {
                "status": "fail",
                "severity": "medium",
                "details": f"{len(missing_controls)} carousel(s) lack visible navigation controls",
                "recommendation": "Add visible previous/next buttons or dot indicators to all carousels"
            }

        return {"status": "pass"}

    def _validate_mobile_carousel(
        self, guideline, soup, html, url, page_data
    ) -> Dict:
        """
        Guideline #957: Avoid Autorotating Carousels on Mobile Homepages.

        Note: This is a static check. Full validation would require
        detecting viewport size and JavaScript autoplay behavior.
        """
        # Check for autoplay attributes
        autoplay_found = 'autoplay' in html.lower()
        data_autoplay = soup.find_all(attrs={'data-autoplay': True})

        if autoplay_found or data_autoplay:
            return {
                "status": "warning",
                "details": "Page contains carousels with autoplay/autorotate features",
                "recommendation": "Disable autorotation on mobile or ensure users can easily pause/control it"
            }

        return {"status": "pass"}

    def _validate_bespoke_imagery(
        self, guideline, soup, html, url, page_data
    ) -> Dict:
        """
        Guideline #238: Always Use Bespoke Imagery and Design.

        Checks for stock photo indicators or placeholder images.
        """
        # Find all images
        images = soup.find_all('img')

        placeholder_indicators = [
            'placeholder', 'dummy', 'stock-photo', 'shutterstock',
            'istock', 'gettyimages', 'lorem', 'sample'
        ]

        placeholder_images = []
        for img in images:
            src = img.get('src', '').lower()
            alt = img.get('alt', '').lower()

            if any(indicator in src or indicator in alt for indicator in placeholder_indicators):
                placeholder_images.append(img)

        if len(placeholder_images) > 0:
            return {
                "status": "fail",
                "severity": "medium",
                "details": f"Found {len(placeholder_images)} placeholder or stock images",
                "recommendation": "Replace all placeholder and stock images with bespoke brand imagery"
            }

        return {"status": "pass"}

    def _validate_current_scope_highlight(
        self, guideline, soup, html, url, page_data
    ) -> Dict:
        """
        Guideline #300: Highlight the Current Scope in the Main Navigation.

        Checks if current page/section is highlighted in navigation.
        """
        # Look for navigation with active/current indicators
        nav_elements = soup.find_all(['nav', 'header'])

        active_indicators_found = False
        for nav in nav_elements:
            # Check for aria-current
            if nav.find_all(attrs={'aria-current': True}):
                active_indicators_found = True
                break

            # Check for common active class names
            active_classes = nav.find_all(class_=re.compile(r'(active|current|selected)', re.I))
            if active_classes:
                active_indicators_found = True
                break

        if not active_indicators_found:
            return {
                "status": "warning",
                "details": "No clear indication of current location in navigation",
                "recommendation": "Add visual highlighting (active class) to current navigation item"
            }

        return {"status": "pass"}

    def _validate_clickable_headings(
        self, guideline, soup, html, url, page_data
    ) -> Dict:
        """
        Guideline #266: Ensure Main Navigation Category Headings Are Clickable Links.

        Checks if navigation headings are clickable.
        """
        # Find navigation menus
        nav_elements = soup.find_all(['nav'])

        non_clickable_headings = []
        for nav in nav_elements:
            # Find potential category headings
            headings = nav.find_all(['h1', 'h2', 'h3', 'h4', 'span', 'div'], class_=re.compile(r'(heading|title|category)', re.I))

            for heading in headings:
                # Check if heading itself is a link or contains a link
                is_link = heading.name == 'a'
                contains_link = heading.find('a') is not None

                if not is_link and not contains_link:
                    # Check if it looks like it should be clickable (has siblings that are links)
                    parent = heading.parent
                    if parent and parent.find_all('a'):
                        non_clickable_headings.append(heading)

        if len(non_clickable_headings) > 2:
            return {
                "status": "fail",
                "severity": "medium",
                "details": f"Found {len(non_clickable_headings)} non-clickable category headings in navigation",
                "recommendation": "Make all category headings in navigation clickable links"
            }

        return {"status": "pass"}

    # Add more validation rules as needed...

    def get_validation_coverage(self) -> Dict:
        """
        Get statistics on validation coverage.

        Returns:
            Dictionary with coverage statistics
        """
        total_guidelines = self.index.get_total_count()
        implemented_rules = len(self.validation_rules)

        return {
            "total_guidelines": total_guidelines,
            "implemented_validations": implemented_rules,
            "coverage_percentage": round((implemented_rules / total_guidelines) * 100, 1),
            "implemented_guideline_ids": list(self.validation_rules.keys()),
        }
