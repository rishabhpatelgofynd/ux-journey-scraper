"""
Tests for Phase 2 native app testing modules.

All tests use mocks — no real device or Appium server required.

Covered:
- MobileStateRegistry  (pHash deduplication)
- NativeElementDetector (accessibility tree scoring)
- GestureEngine         (touch primitives)
- AppiumSession         (capability building + server validation)
- AppiumCrawler         (end-to-end crawl orchestration)
- NativeAppConfig / PlatformConfig native variants
"""
import asyncio
import base64
import io
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest
from PIL import Image

from ux_journey_scraper.config.scrape_config import (
    NativeAppConfig,
    PlatformConfig,
    ScrapeConfig,
    AuthConfig,
    CrawlerConfig,
)
from ux_journey_scraper.core.mobile_state_registry import MobileStateRegistry
from ux_journey_scraper.core.native_element_detector import (
    NativeElement,
    NativeElementDetector,
)
from ux_journey_scraper.core.gesture_engine import GestureEngine
from ux_journey_scraper.core.appium_session import AppiumSession
from ux_journey_scraper.core.appium_crawler import AppiumCrawler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_png_b64(color=(255, 0, 0), size=(10, 10)) -> str:
    """Return a base64-encoded PNG with a solid colour."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _native_android_platform(pkg="com.example.app") -> PlatformConfig:
    return PlatformConfig(
        type="native_android",
        native=NativeAppConfig(
            app_package=pkg,
            appium_server="http://localhost:4723",
        ),
    )


def _native_ios_platform(bundle="com.example.App") -> PlatformConfig:
    return PlatformConfig(
        type="native_ios",
        native=NativeAppConfig(
            bundle_id=bundle,
            appium_server="http://localhost:4723",
        ),
    )


def _make_scrape_config(platform: PlatformConfig) -> ScrapeConfig:
    return ScrapeConfig(
        target={"name": "Test App", "base_url": "https://example.com"},
        platforms=[platform],
        auth=AuthConfig(logged_out=True, logged_in=False),
        seed_urls=["https://example.com"],
        crawler=CrawlerConfig(max_pages=3),
    )


# ---------------------------------------------------------------------------
# NativeAppConfig & PlatformConfig
# ---------------------------------------------------------------------------

class TestNativeAppConfig:
    """Config-level tests for native platform support."""

    def test_native_android_requires_package_or_apk(self):
        """native_android without app_package or apk_path must raise."""
        with pytest.raises(ValueError, match="app_package.*apk_path"):
            PlatformConfig(type="native_android", native=NativeAppConfig())

    def test_native_ios_requires_bundle_or_ipa(self):
        """native_ios without bundle_id or ipa_path must raise."""
        with pytest.raises(ValueError, match="bundle_id.*ipa_path"):
            PlatformConfig(type="native_ios", native=NativeAppConfig())

    def test_native_android_without_native_block_raises(self):
        """native_android without a native: block must raise."""
        with pytest.raises(ValueError, match="native.*configuration"):
            PlatformConfig(type="native_android")

    def test_valid_native_android(self):
        p = _native_android_platform()
        assert p.is_native is True
        assert p.is_web is False
        assert p.native.app_package == "com.example.app"

    def test_valid_native_ios(self):
        p = _native_ios_platform()
        assert p.is_native is True
        assert p.is_web is False
        assert p.native.bundle_id == "com.example.App"

    def test_native_android_via_apk_path(self):
        """apk_path alone is sufficient for native_android."""
        p = PlatformConfig(
            type="native_android",
            native=NativeAppConfig(apk_path="/tmp/app.apk"),
        )
        assert p.is_native is True

    def test_native_ios_via_ipa_path(self):
        """ipa_path alone is sufficient for native_ios."""
        p = PlatformConfig(
            type="native_ios",
            native=NativeAppConfig(ipa_path="/tmp/app.ipa"),
        )
        assert p.is_native is True

    def test_web_platform_is_not_native(self):
        p = PlatformConfig(type="web_mobile", viewport={"width": 390, "height": 844})
        assert p.is_native is False
        assert p.is_web is True

    def test_web_platform_still_requires_viewport(self):
        with pytest.raises(ValueError, match="viewport"):
            PlatformConfig(type="web_desktop")


# ---------------------------------------------------------------------------
# MobileStateRegistry
# ---------------------------------------------------------------------------

class TestMobileStateRegistry:
    """Tests for perceptual-hash based screen deduplication."""

    def test_unseen_screen_returns_false(self):
        reg = MobileStateRegistry()
        b64 = _make_png_b64()
        assert reg.has_seen(b64, "btn1|btn2") is False

    def test_seen_after_register(self):
        reg = MobileStateRegistry()
        b64 = _make_png_b64()
        reg.register(b64, "btn1|btn2")
        assert reg.has_seen(b64, "btn1|btn2") is True

    def test_different_summary_is_different_state(self):
        reg = MobileStateRegistry()
        b64 = _make_png_b64()
        reg.register(b64, "btn1|btn2")
        assert reg.has_seen(b64, "btn3|btn4") is False

    def test_different_screenshot_is_different_state(self):
        """Two visually distinct images must produce different keys."""
        reg = MobileStateRegistry()

        # Create two images with opposite checker patterns so pHash differs
        def _checker(fill, bg, size=64):
            img = Image.new("RGB", (size, size), color=bg)
            for y in range(0, size, 8):
                for x in range(0, size, 8):
                    if (x // 8 + y // 8) % 2 == 0:
                        for py in range(y, min(y + 8, size)):
                            for px in range(x, min(x + 8, size)):
                                img.putpixel((px, py), fill)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()

        b64_a = _checker(fill=(255, 255, 255), bg=(0, 0, 0))
        b64_b = _checker(fill=(0, 0, 0), bg=(255, 255, 255))

        reg.register(b64_a, "summary")
        assert reg.has_seen(b64_b, "summary") is False

    def test_size_increments(self):
        reg = MobileStateRegistry()
        assert reg.size() == 0
        reg.register(_make_png_b64(color=(255, 0, 0)), "a")
        reg.register(_make_png_b64(color=(0, 255, 0)), "b")
        assert reg.size() == 2

    def test_duplicate_register_does_not_grow_size(self):
        reg = MobileStateRegistry()
        b64 = _make_png_b64()
        reg.register(b64, "x")
        reg.register(b64, "x")
        assert reg.size() == 1

    def test_fallback_to_md5_when_imagehash_unavailable(self):
        """Registry still works when imagehash is patched out."""
        reg = MobileStateRegistry()
        b64 = _make_png_b64()
        with patch(
            "ux_journey_scraper.core.mobile_state_registry._IMAGEHASH_AVAILABLE",
            False,
        ):
            reg.register(b64, "summary")
            assert reg.has_seen(b64, "summary") is True


# ---------------------------------------------------------------------------
# NativeElementDetector
# ---------------------------------------------------------------------------

class TestNativeElementDetector:
    """Tests for accessibility tree element detection and scoring."""

    def _el(self, text, el_type="android.widget.Button") -> NativeElement:
        return NativeElement(
            element_id="id1",
            text=text,
            element_type=el_type,
            bounds={"x": 0, "y": 0, "width": 100, "height": 44},
        )

    # -- score() --

    def test_score_add_to_cart(self):
        det = NativeElementDetector()
        assert det.score(self._el("Add to Cart")) == 100

    def test_score_buy_now(self):
        det = NativeElementDetector()
        assert det.score(self._el("Buy Now")) == 95

    def test_score_checkout(self):
        det = NativeElementDetector()
        assert det.score(self._el("Checkout")) == 90

    def test_score_continue(self):
        det = NativeElementDetector()
        assert det.score(self._el("Continue")) == 80

    def test_score_unknown_text_returns_default(self):
        det = NativeElementDetector()
        assert det.score(self._el("Foobar XYZ")) == 10

    def test_score_case_insensitive(self):
        det = NativeElementDetector()
        assert det.score(self._el("ADD TO CART")) == 100

    def test_score_partial_match(self):
        det = NativeElementDetector()
        # "checkout" is a substring of "Proceed to Checkout"
        assert det.score(self._el("Proceed to Checkout")) == 90

    # -- is_flutter_only() --

    def test_flutter_only_all_generic_ios_no_text(self):
        det = NativeElementDetector()
        elements = [
            NativeElement("1", "", "XCUIElementTypeOther", {}),
            NativeElement("2", "", "XCUIElementTypeOther", {}),
        ]
        assert det.is_flutter_only(elements, "native_ios") is True

    def test_flutter_only_all_generic_android_no_text(self):
        det = NativeElementDetector()
        elements = [
            NativeElement("1", "", "android.view.View", {}),
            NativeElement("2", "", "android.view.View", {}),
        ]
        assert det.is_flutter_only(elements, "native_android") is True

    def test_not_flutter_if_real_button_type(self):
        det = NativeElementDetector()
        elements = [
            NativeElement("1", "", "XCUIElementTypeButton", {}),
        ]
        assert det.is_flutter_only(elements, "native_ios") is False

    def test_not_flutter_if_element_has_text(self):
        det = NativeElementDetector()
        elements = [
            NativeElement("1", "Add to Cart", "XCUIElementTypeOther", {}),
        ]
        assert det.is_flutter_only(elements, "native_ios") is False

    def test_empty_elements_is_flutter_only(self):
        det = NativeElementDetector()
        assert det.is_flutter_only([], "native_ios") is True

    # -- find_interactive() with mock driver --

    def test_find_interactive_android_returns_sorted_by_priority(self):
        det = NativeElementDetector()

        low_el = MagicMock()
        low_el.text = "Terms"
        low_el.get_attribute.return_value = "android.widget.TextView"
        low_el.location = {"x": 0, "y": 0}
        low_el.size = {"width": 100, "height": 44}
        low_el.id = "el-low"

        high_el = MagicMock()
        high_el.text = "Add to Cart"
        high_el.get_attribute.return_value = "android.widget.Button"
        high_el.location = {"x": 0, "y": 50}
        high_el.size = {"width": 100, "height": 44}
        high_el.id = "el-high"

        driver = MagicMock()
        driver.find_elements.return_value = [low_el, high_el]

        results = det.find_interactive(driver, "native_android")

        assert results[0].text == "Add to Cart"
        assert results[0].priority == 100
        assert results[1].text == "Terms"
        assert results[1].priority == 10

    def test_find_interactive_returns_empty_on_driver_error(self):
        det = NativeElementDetector()
        driver = MagicMock()
        driver.find_elements.side_effect = Exception("connection lost")
        results = det.find_interactive(driver, "native_android")
        assert results == []


# ---------------------------------------------------------------------------
# GestureEngine
# ---------------------------------------------------------------------------

class TestGestureEngine:
    """Tests for touch gesture primitives."""

    def test_tap_calls_element_click(self):
        engine = GestureEngine()
        driver = MagicMock()
        element = MagicMock()
        engine.tap(driver, element)
        element.click.assert_called_once()

    def test_scroll_down_ios_uses_execute_script(self):
        engine = GestureEngine()
        driver = MagicMock()
        engine.scroll_down(driver, "native_ios")
        driver.execute_script.assert_called_once_with(
            "mobile: scroll", {"direction": "down"}
        )

    def test_scroll_down_android_does_not_call_execute_script(self):
        engine = GestureEngine()
        driver = MagicMock()
        driver.get_window_size.return_value = {"width": 390, "height": 844}
        engine.scroll_down(driver, "native_android")
        driver.execute_script.assert_not_called()

    def test_swipe_back_android_presses_back_key(self):
        engine = GestureEngine()
        driver = MagicMock()
        engine.swipe_back(driver, "native_android")
        driver.press_keycode.assert_called_once_with(4)

    def test_swipe_back_ios_does_not_press_keycode(self):
        engine = GestureEngine()
        driver = MagicMock()
        driver.get_window_size.return_value = {"width": 390, "height": 844}
        engine.swipe_back(driver, "native_ios")
        driver.press_keycode.assert_not_called()

    def test_dismiss_keyboard_ios_uses_execute_script(self):
        engine = GestureEngine()
        driver = MagicMock()
        engine.dismiss_keyboard(driver, "native_ios")
        driver.execute_script.assert_called_once_with("mobile: hideKeyboard")

    def test_dismiss_keyboard_android_uses_hide_keyboard(self):
        engine = GestureEngine()
        driver = MagicMock()
        engine.dismiss_keyboard(driver, "native_android")
        driver.hide_keyboard.assert_called_once()

    def test_gestures_swallow_driver_errors_gracefully(self):
        """Gesture failures must not propagate exceptions."""
        engine = GestureEngine()
        driver = MagicMock()
        driver.execute_script.side_effect = Exception("WebDriverException")
        driver.get_window_size.return_value = {"width": 390, "height": 844}
        # Should not raise
        engine.scroll_down(driver, "native_ios")
        engine.swipe_back(driver, "native_ios")


# ---------------------------------------------------------------------------
# AppiumSession
# ---------------------------------------------------------------------------

class TestAppiumSession:
    """Tests for capability building and server validation."""

    # -- capability builders --

    def test_android_caps_with_package_and_activity(self):
        session = AppiumSession()
        n = NativeAppConfig(
            app_package="com.example.app",
            app_activity=".MainActivity",
            device_name="Pixel 7",
            platform_version="14.0",
        )
        caps = session._android_caps(n)
        assert caps["platformName"] == "Android"
        assert caps["automationName"] == "UiAutomator2"
        assert caps["appPackage"] == "com.example.app"
        assert caps["appActivity"] == ".MainActivity"
        assert caps["deviceName"] == "Pixel 7"
        assert caps["platformVersion"] == "14.0"
        assert caps["noReset"] is True

    def test_android_caps_with_apk_path(self):
        session = AppiumSession()
        n = NativeAppConfig(apk_path="/tmp/app.apk")
        caps = session._android_caps(n)
        assert caps["app"] == "/tmp/app.apk"
        assert "appPackage" not in caps

    def test_android_caps_with_avd(self):
        session = AppiumSession()
        n = NativeAppConfig(app_package="com.ex.app", avd_name="Pixel_7_API_34")
        caps = session._android_caps(n)
        assert caps["avd"] == "Pixel_7_API_34"

    def test_ios_caps_with_bundle_id(self):
        session = AppiumSession()
        n = NativeAppConfig(
            bundle_id="com.example.App",
            device_name="iPhone 15 Pro",
            platform_version="17.4",
            simulator_udid="XXXX-YYYY",
        )
        caps = session._ios_caps(n)
        assert caps["platformName"] == "iOS"
        assert caps["automationName"] == "XCUITest"
        assert caps["bundleId"] == "com.example.App"
        assert caps["deviceName"] == "iPhone 15 Pro"
        assert caps["platformVersion"] == "17.4"
        assert caps["udid"] == "XXXX-YYYY"
        assert caps["noReset"] is True

    def test_ios_caps_with_ipa_path(self):
        session = AppiumSession()
        n = NativeAppConfig(ipa_path="/tmp/app.ipa")
        caps = session._ios_caps(n)
        assert caps["app"] == "/tmp/app.ipa"
        assert "bundleId" not in caps

    # -- _validate_server --

    def test_validate_server_raises_on_connection_error(self):
        import requests
        session = AppiumSession()
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(RuntimeError, match="Cannot connect to Appium"):
                session._validate_server("http://localhost:4723")

    def test_validate_server_raises_on_timeout(self):
        import requests
        session = AppiumSession()
        with patch("requests.get", side_effect=requests.exceptions.Timeout):
            with pytest.raises(RuntimeError, match="did not respond"):
                session._validate_server("http://localhost:4723")

    def test_validate_server_passes_on_200(self):
        session = AppiumSession()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_resp):
            session._validate_server("http://localhost:4723")  # should not raise

    # -- create_driver --

    def test_create_driver_android_calls_remote(self):
        session = AppiumSession()
        platform = _native_android_platform()
        mock_driver = MagicMock()

        with patch.object(session, "_validate_server"), \
             patch(
                "ux_journey_scraper.core.appium_session.appium_webdriver.Remote",
                return_value=mock_driver,
             ) as mock_remote:
            driver = session.create_driver(platform)
            assert driver is mock_driver
            call_args = mock_remote.call_args
            assert call_args[0][0] == "http://localhost:4723"
            caps = call_args[0][1]
            assert caps["platformName"] == "Android"

    def test_create_driver_ios_calls_remote(self):
        session = AppiumSession()
        platform = _native_ios_platform()
        mock_driver = MagicMock()

        with patch.object(session, "_validate_server"), \
             patch(
                "ux_journey_scraper.core.appium_session.appium_webdriver.Remote",
                return_value=mock_driver,
             ) as mock_remote:
            driver = session.create_driver(platform)
            caps = mock_remote.call_args[0][1]
            assert caps["platformName"] == "iOS"


# ---------------------------------------------------------------------------
# AppiumCrawler
# ---------------------------------------------------------------------------

class TestAppiumCrawler:
    """Integration-style tests using a fully mocked Appium driver."""

    def _make_mock_driver(self, screenshot_b64=None, contexts=None):
        """Build a mock Appium driver for crawl tests."""
        driver = MagicMock()
        driver.get_screenshot_as_base64.return_value = (
            screenshot_b64 or _make_png_b64()
        )
        driver.contexts = contexts or ["NATIVE_APP"]
        driver.find_elements.return_value = []
        driver.get_window_size.return_value = {"width": 390, "height": 844}
        return driver

    def _make_arch(self, arch_type="native"):
        from ux_journey_scraper.core.app_architecture_detector import (
            ArchitectureDetectionResult,
        )
        return ArchitectureDetectionResult(
            architecture=arch_type,
            confidence=0.9,
            evidence=[],
            platform="android",
            metadata={},
        )

    # -- get_stats --

    def test_get_stats_initial(self):
        platform = _native_android_platform()
        config = _make_scrape_config(platform)
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AppiumCrawler(config, tmpdir, platform)
            stats = crawler.get_stats()
            assert stats["pages_captured"] == 0
            assert stats["unique_states"] == 0

    # -- _capture_screen --

    @pytest.mark.asyncio
    async def test_capture_screen_saves_png(self):
        platform = _native_android_platform()
        config = _make_scrape_config(platform)
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AppiumCrawler(config, tmpdir, platform)
            driver = self._make_mock_driver()

            step = await crawler._capture_screen(driver, 0, "test-screen")

            assert step.step_number == 0
            assert step.title == "test-screen"
            assert step.url == ""
            assert Path(step.screenshot_path).exists()
            assert step.screenshot_path.endswith("step-000.png")

    # -- _handle_permission_dialog --

    @pytest.mark.asyncio
    async def test_permission_dialog_ios_allow_button_clicked(self):
        platform = _native_ios_platform()
        config = _make_scrape_config(platform)
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AppiumCrawler(config, tmpdir, platform)
            driver = MagicMock()
            allow_btn = MagicMock()
            driver.find_element.return_value = allow_btn

            await crawler._handle_permission_dialog(driver)

            driver.find_element.assert_called()
            allow_btn.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_permission_dialog_android_allow_button_clicked(self):
        platform = _native_android_platform()
        config = _make_scrape_config(platform)
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AppiumCrawler(config, tmpdir, platform)
            driver = MagicMock()
            allow_btn = MagicMock()
            driver.find_element.return_value = allow_btn

            await crawler._handle_permission_dialog(driver)

            driver.find_element.assert_called_once_with(
                "id",
                "com.android.permissioncontroller:id/permission_allow_button",
            )
            allow_btn.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_permission_dialog_error_does_not_raise(self):
        """Failure to find dialog must be silently ignored."""
        platform = _native_android_platform()
        config = _make_scrape_config(platform)
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AppiumCrawler(config, tmpdir, platform)
            driver = MagicMock()
            driver.find_element.side_effect = Exception("element not found")
            await crawler._handle_permission_dialog(driver)  # must not raise

    # -- crawl() routing --

    @pytest.mark.asyncio
    async def test_crawl_native_arch_returns_journey(self):
        platform = _native_android_platform()
        config = _make_scrape_config(platform)
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AppiumCrawler(config, tmpdir, platform)
            driver = self._make_mock_driver()

            with patch(
                "ux_journey_scraper.core.appium_crawler.AppiumSession.create_driver",
                return_value=driver,
            ), patch(
                "ux_journey_scraper.core.appium_crawler.AppArchitectureDetector.detect",
                new_callable=AsyncMock,
                return_value=self._make_arch("native"),
            ):
                journey = await crawler.crawl()

            assert journey is not None
            assert journey.end_time is not None

    @pytest.mark.asyncio
    async def test_crawl_webview_arch_switches_context(self):
        platform = _native_android_platform()
        config = _make_scrape_config(platform)
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AppiumCrawler(config, tmpdir, platform)
            driver = self._make_mock_driver(
                contexts=["NATIVE_APP", "WEBVIEW_com.example.app"]
            )
            # WebView DOM elements for the web crawl path
            mock_el = MagicMock()
            mock_el.text = "Shop Now"
            mock_el.is_displayed.return_value = True
            mock_el.is_enabled.return_value = True
            driver.find_elements.return_value = [mock_el]

            with patch(
                "ux_journey_scraper.core.appium_crawler.AppiumSession.create_driver",
                return_value=driver,
            ), patch(
                "ux_journey_scraper.core.appium_crawler.AppArchitectureDetector.detect",
                new_callable=AsyncMock,
                return_value=self._make_arch("webview"),
            ):
                journey = await crawler.crawl()

            driver.switch_to.context.assert_called()
            call_arg = driver.switch_to.context.call_args[0][0]
            assert "WEBVIEW" in call_arg

    @pytest.mark.asyncio
    async def test_crawl_driver_quit_called_on_error(self):
        """driver.quit() must be called even when crawl raises."""
        platform = _native_android_platform()
        config = _make_scrape_config(platform)
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AppiumCrawler(config, tmpdir, platform)
            driver = self._make_mock_driver()

            with patch(
                "ux_journey_scraper.core.appium_crawler.AppiumSession.create_driver",
                return_value=driver,
            ), patch(
                "ux_journey_scraper.core.appium_crawler.AppArchitectureDetector.detect",
                new_callable=AsyncMock,
                side_effect=RuntimeError("boom"),
            ):
                journey = await crawler.crawl()

            driver.quit.assert_called_once()
            # Should return an empty journey, not raise
            assert journey is not None

    @pytest.mark.asyncio
    async def test_crawl_flutter_mode_scrolls_only(self):
        """When all elements are generic view types, crawler uses scroll-only mode."""
        platform = _native_ios_platform()
        config = _make_scrape_config(platform)
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AppiumCrawler(config, tmpdir, platform)

            # Build unique screenshots so dedup doesn't stop after 1 step
            screenshots = [
                _make_png_b64(color=(i * 40, 0, 0)) for i in range(5)
            ]
            call_count = {"n": 0}

            def next_screenshot():
                idx = min(call_count["n"], len(screenshots) - 1)
                call_count["n"] += 1
                return screenshots[idx]

            driver = MagicMock()
            driver.get_screenshot_as_base64.side_effect = next_screenshot
            driver.get_window_size.return_value = {"width": 390, "height": 844}

            # Flutter-style elements: all XCUIElementTypeOther, no text
            flutter_el = MagicMock()
            flutter_el.text = ""
            flutter_el.get_attribute.return_value = "XCUIElementTypeOther"
            flutter_el.location = {"x": 0, "y": 0}
            flutter_el.size = {"width": 390, "height": 50}
            flutter_el.id = "fl-1"
            driver.find_elements.return_value = [flutter_el]

            with patch(
                "ux_journey_scraper.core.appium_crawler.AppiumSession.create_driver",
                return_value=driver,
            ), patch(
                "ux_journey_scraper.core.appium_crawler.AppArchitectureDetector.detect",
                new_callable=AsyncMock,
                return_value=self._make_arch("native"),
            ):
                journey = await crawler.crawl()

            # Should have captured pages and scrolled (not tapped)
            assert len(journey.steps) > 0
            # execute_script called for iOS scroll
            driver.execute_script.assert_called()

    @pytest.mark.asyncio
    async def test_crawl_dedup_triggers_swipe_back(self):
        """Seeing the same screen repeatedly triggers back navigation."""
        platform = _native_android_platform()
        config = _make_scrape_config(platform)
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AppiumCrawler(config, tmpdir, platform)

            # Same screenshot every call → dedup fires immediately after first register
            fixed_b64 = _make_png_b64()
            driver = self._make_mock_driver(screenshot_b64=fixed_b64)

            with patch(
                "ux_journey_scraper.core.appium_crawler.AppiumSession.create_driver",
                return_value=driver,
            ), patch(
                "ux_journey_scraper.core.appium_crawler.AppArchitectureDetector.detect",
                new_callable=AsyncMock,
                return_value=self._make_arch("native"),
            ):
                await crawler.crawl()

            # BACK key should have been pressed (Android swipe_back = press_keycode(4))
            driver.press_keycode.assert_called_with(4)

    def test_pages_captured_increments(self):
        """get_stats() pages_captured should reflect crawl progress."""
        platform = _native_android_platform()
        config = _make_scrape_config(platform)
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AppiumCrawler(config, tmpdir, platform)
            crawler.pages_captured = 5
            assert crawler.get_stats()["pages_captured"] == 5
