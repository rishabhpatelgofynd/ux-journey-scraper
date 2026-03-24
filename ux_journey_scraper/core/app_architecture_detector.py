"""
App Architecture Detector - Detects if mobile app is native, WebView, or hybrid.

Detects mobile app architecture type for Android and iOS apps.
Public module - contains NO proprietary Baymard data.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ArchitectureDetectionResult:
    """
    Result of app architecture detection.

    Attributes:
        architecture: Architecture type ('native', 'webview', 'hybrid', or 'unknown')
        confidence: Confidence score 0.0-1.0
        evidence: List of detection signals
        platform: Platform ('android' or 'ios')
        metadata: Additional detection metadata
    """

    architecture: str
    confidence: float
    evidence: List[str]
    platform: str
    metadata: Dict


class AppArchitectureDetector:
    """
    Detects mobile app architecture (native, WebView, or hybrid).

    Detection methods:
    1. Context switching (NATIVE_APP vs WEBVIEW contexts)
    2. DOM accessibility (can access HTML elements)
    3. View hierarchy analysis (native widgets vs WebView)
    4. JavaScript execution (can inject and run JS)
    5. Performance characteristics

    Works with Appium WebDriver for both Android and iOS.
    """

    def __init__(self):
        """Initialize architecture detector."""
        pass

    async def detect(self, driver) -> ArchitectureDetectionResult:
        """
        Detect app architecture.

        Args:
            driver: Appium WebDriver instance

        Returns:
            ArchitectureDetectionResult with architecture type and confidence
        """
        # Detect platform first
        platform = self._detect_platform(driver)

        logger.info(f"🔍 Detecting app architecture for {platform}")

        evidence = []
        scores = {
            "native": 0.0,
            "webview": 0.0,
            "hybrid": 0.0,
        }

        # Method 1: Context Switching Detection (50% weight)
        context_scores = await self._detect_from_contexts(driver, platform)
        for arch_type, score in context_scores.items():
            scores[arch_type] += score * 0.50
            if score > 0:
                evidence.append(
                    f"Context analysis indicates {arch_type} (score: {score:.2f})"
                )

        # Method 2: DOM Accessibility (25% weight)
        dom_scores = await self._detect_from_dom_access(driver, platform)
        for arch_type, score in dom_scores.items():
            scores[arch_type] += score * 0.25
            if score > 0:
                evidence.append(
                    f"DOM accessibility indicates {arch_type} (score: {score:.2f})"
                )

        # Method 3: View Hierarchy Analysis (15% weight)
        hierarchy_scores = await self._detect_from_view_hierarchy(driver, platform)
        for arch_type, score in hierarchy_scores.items():
            scores[arch_type] += score * 0.15
            if score > 0:
                evidence.append(
                    f"View hierarchy indicates {arch_type} (score: {score:.2f})"
                )

        # Method 4: JavaScript Execution (10% weight)
        js_scores = await self._detect_from_js_execution(driver, platform)
        for arch_type, score in js_scores.items():
            scores[arch_type] += score * 0.10
            if score > 0:
                evidence.append(
                    f"JavaScript execution indicates {arch_type} (score: {score:.2f})"
                )

        # Determine architecture
        detected_type = max(scores, key=scores.get)
        confidence = min(scores[detected_type], 1.0)

        # If confidence too low, mark as unknown
        if confidence < 0.3:
            detected_type = "unknown"
            evidence.append(f"Low confidence ({confidence:.2f}) - architecture unclear")

        logger.info(
            f"✓ Architecture detected: {detected_type} "
            f"(platform: {platform}, confidence: {confidence:.2f})"
        )

        return ArchitectureDetectionResult(
            architecture=detected_type,
            confidence=confidence,
            evidence=evidence,
            platform=platform,
            metadata={"all_scores": scores},
        )

    def _detect_platform(self, driver) -> str:
        """
        Detect platform from driver capabilities.

        Args:
            driver: Appium WebDriver

        Returns:
            Platform string ('android' or 'ios')
        """
        try:
            capabilities = driver.capabilities
            platform = capabilities.get("platformName", "").lower()

            if "android" in platform:
                return "android"
            elif "ios" in platform:
                return "ios"
            else:
                # Try to infer from other capabilities
                if "appPackage" in capabilities:
                    return "android"
                elif "bundleId" in capabilities:
                    return "ios"

                logger.warning(
                    f"Could not detect platform from capabilities: {capabilities}"
                )
                return "android"  # Default

        except Exception as e:
            logger.warning(f"Error detecting platform: {e}")
            return "android"

    async def _detect_from_contexts(self, driver, platform: str) -> Dict[str, float]:
        """
        Detect architecture from available contexts.

        Native apps: Only NATIVE_APP context
        WebView apps: NATIVE_APP + WEBVIEW contexts
        Hybrid apps: NATIVE_APP + multiple WEBVIEW contexts

        Args:
            driver: Appium WebDriver
            platform: Platform ('android' or 'ios')

        Returns:
            Dict mapping architecture types to scores
        """
        scores = {"native": 0.0, "webview": 0.0, "hybrid": 0.0}

        try:
            # Get available contexts
            contexts = driver.contexts

            logger.debug(f"Available contexts: {contexts}")

            # Count context types
            native_contexts = [c for c in contexts if "NATIVE_APP" in c]
            webview_contexts = [
                c for c in contexts if "WEBVIEW" in c or "CHROMIUM" in c
            ]

            if len(webview_contexts) == 0:
                # Only native context = fully native app
                scores["native"] = 1.0
                logger.debug("No WebView contexts - fully native app")

            elif len(webview_contexts) == 1:
                # One WebView context = likely WebView wrapper
                scores["webview"] = 0.9
                scores["hybrid"] = 0.1
                logger.debug("Single WebView context - likely WebView wrapper")

            elif len(webview_contexts) > 1:
                # Multiple WebView contexts = hybrid app
                scores["hybrid"] = 0.9
                scores["webview"] = 0.1
                logger.debug(f"{len(webview_contexts)} WebView contexts - hybrid app")

        except Exception as e:
            logger.debug(f"Error detecting from contexts: {e}")
            # If can't get contexts, inconclusive
            scores["native"] = 0.5

        return scores

    async def _detect_from_dom_access(self, driver, platform: str) -> Dict[str, float]:
        """
        Detect architecture by trying to access DOM.

        Native apps: Cannot access DOM
        WebView/Hybrid apps: Can access DOM via CSS selectors

        Args:
            driver: Appium WebDriver
            platform: Platform

        Returns:
            Dict mapping architecture types to scores
        """
        scores = {"native": 0.0, "webview": 0.0, "hybrid": 0.0}

        try:
            # Try to find elements using CSS selectors
            # WebView apps will have HTML elements
            elements = driver.find_elements("css selector", "body")

            if len(elements) > 0:
                # Can access DOM = WebView or hybrid
                scores["webview"] = 0.8
                scores["hybrid"] = 0.2
                logger.debug("Can access DOM - WebView or hybrid")
            else:
                # No DOM elements = likely native
                scores["native"] = 0.8
                logger.debug("Cannot access DOM - likely native")

        except Exception as e:
            # Exception trying to access DOM = likely native
            scores["native"] = 0.7
            logger.debug(f"DOM access failed (likely native): {e}")

        return scores

    async def _detect_from_view_hierarchy(
        self, driver, platform: str
    ) -> Dict[str, float]:
        """
        Detect architecture from view hierarchy.

        Native apps: Native widgets (Button, TextView, etc.)
        WebView apps: WebView in hierarchy

        Args:
            driver: Appium WebDriver
            platform: Platform

        Returns:
            Dict mapping architecture types to scores
        """
        scores = {"native": 0.0, "webview": 0.0, "hybrid": 0.0}

        try:
            # Get page source
            page_source = driver.page_source.lower()

            # Check for WebView indicators
            webview_indicators = [
                "webview",
                "chromium",
                "web-view",
                "uiwebview",
                "wkwebview",
            ]
            webview_count = sum(
                1 for indicator in webview_indicators if indicator in page_source
            )

            if webview_count > 0:
                # WebView present in hierarchy
                scores["webview"] = min(webview_count / 3, 0.9)
                scores["hybrid"] = 0.1
                logger.debug(
                    f"WebView detected in hierarchy ({webview_count} indicators)"
                )
            else:
                # No WebView in hierarchy = likely native
                scores["native"] = 0.8
                logger.debug("No WebView in hierarchy - likely native")

        except Exception as e:
            logger.debug(f"Error analyzing view hierarchy: {e}")

        return scores

    async def _detect_from_js_execution(
        self, driver, platform: str
    ) -> Dict[str, float]:
        """
        Detect architecture by trying to execute JavaScript.

        Native apps: Cannot execute JS
        WebView/Hybrid apps: Can execute JS

        Args:
            driver: Appium WebDriver
            platform: Platform

        Returns:
            Dict mapping architecture types to scores
        """
        scores = {"native": 0.0, "webview": 0.0, "hybrid": 0.0}

        try:
            # Try to execute simple JavaScript
            result = driver.execute_script("return typeof window;")

            if result == "object":
                # Can execute JS and access window = WebView or hybrid
                scores["webview"] = 0.7
                scores["hybrid"] = 0.3
                logger.debug("JavaScript execution successful - WebView or hybrid")
            else:
                scores["native"] = 0.6
                logger.debug("JavaScript execution returned unexpected result")

        except Exception as e:
            # Cannot execute JS = likely native
            scores["native"] = 0.8
            logger.debug(f"JavaScript execution failed (likely native): {e}")

        return scores

    async def detect_with_implications(self, driver) -> Dict:
        """
        Detect architecture and provide testing implications.

        Args:
            driver: Appium WebDriver

        Returns:
            Dict with architecture, confidence, and testing implications
        """
        result = await self.detect(driver)

        # Add testing implications based on architecture
        implications = []

        if result.architecture == "native":
            implications = [
                "Test all UX checks - fully native implementation",
                "Performance likely optimal",
                "Platform-specific UI patterns expected",
                "No web version cross-reference needed",
            ]
        elif result.architecture == "webview":
            implications = [
                "Test all UX checks - UI interactions differ from web",
                "Check if issues also exist on mobile web",
                "Touch interactions may differ from web",
                "Performance may be slower than native",
                "Fixing web version may fix app version",
            ]
        elif result.architecture == "hybrid":
            implications = [
                "Test all UX checks - mixed implementation",
                "Some screens native, some WebView",
                "Test transitions between native and WebView",
                "Performance varies by screen type",
            ]
        else:
            implications = [
                "Architecture unclear - test comprehensively",
                "May need manual inspection",
            ]

        return {
            "architecture": result.architecture,
            "confidence": result.confidence,
            "evidence": result.evidence,
            "platform": result.platform,
            "implications": implications,
            "metadata": result.metadata,
        }


# Convenience function
async def detect_architecture(driver) -> ArchitectureDetectionResult:
    """
    Convenience function to detect app architecture.

    Args:
        driver: Appium WebDriver instance

    Returns:
        ArchitectureDetectionResult
    """
    detector = AppArchitectureDetector()
    return await detector.detect(driver)
