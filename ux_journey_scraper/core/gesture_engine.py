"""
Touch gesture primitives for Appium-based mobile crawling.

Provides tap, scroll, swipe, long press, pull-to-refresh, and keyboard dismissal
for both Android (UiAutomator2) and iOS (XCUITest).
"""
import logging
import time

logger = logging.getLogger(__name__)


class GestureEngine:
    """
    Executes touch gestures on native mobile apps via Appium.

    Supports Android (UiAutomator2) and iOS (XCUITest) with platform-specific
    implementations where the gesture APIs differ.
    """

    def tap(self, driver, element) -> None:
        """
        Tap a native element.

        Args:
            driver: Appium WebDriver (unused, kept for uniform API)
            element: Appium WebElement to tap
        """
        element.click()

    def scroll_down(self, driver, platform_type: str, pixels: int = 500) -> None:
        """
        Scroll the current view downward.

        Args:
            driver: Appium WebDriver
            platform_type: "native_android" or "native_ios"
            pixels: Approximate scroll distance in pixels
        """
        if platform_type == "native_ios":
            try:
                driver.execute_script("mobile: scroll", {"direction": "down"})
            except Exception as exc:
                logger.debug(f"iOS scroll failed, falling back to swipe: {exc}")
                self._ios_swipe_up(driver, pixels)
        else:
            self._android_scroll_down(driver, pixels)

    def swipe_back(self, driver, platform_type: str) -> None:
        """
        Navigate back.

        On iOS this performs an edge-swipe from the left; on Android it presses
        the hardware BACK key (keycode 4).

        Args:
            driver: Appium WebDriver
            platform_type: "native_android" or "native_ios"
        """
        if platform_type == "native_ios":
            self._ios_edge_swipe_back(driver)
        else:
            try:
                driver.press_keycode(4)  # Android BACK key
            except Exception as exc:
                logger.debug(f"Android BACK keycode failed: {exc}")

    def pull_to_refresh(self, driver, platform_type: str) -> None:
        """
        Pull-to-refresh gesture (drag list from top downward).

        Args:
            driver: Appium WebDriver
            platform_type: "native_android" or "native_ios"
        """
        try:
            size = driver.get_window_size()
            width = size["width"]
            height = size["height"]
            start_x = width // 2
            start_y = int(height * 0.2)
            end_y = int(height * 0.6)

            if platform_type == "native_ios":
                driver.execute_script("mobile: dragFromToForDuration", {
                    "fromX": start_x, "fromY": start_y,
                    "toX": start_x, "toY": end_y,
                    "duration": 1.0,
                })
            else:
                self._w3c_swipe(driver, start_x, start_y, start_x, end_y, duration_ms=800)
        except Exception as exc:
            logger.debug(f"pull_to_refresh failed: {exc}")

    def long_press(self, driver, element, duration_ms: int = 1000) -> None:
        """
        Long-press on a native element using W3C Actions.

        Args:
            driver: Appium WebDriver
            element: Appium WebElement to long-press
            duration_ms: Press duration in milliseconds
        """
        try:
            from appium.webdriver.common.appiumby import AppiumBy
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.common.actions.action_builder import ActionBuilder
            from selenium.webdriver.common.actions.pointer_input import PointerInput
            from selenium.webdriver.common.actions import interaction

            actions = ActionChains(driver)
            actions.w3c_actions = ActionBuilder(
                driver,
                mouse=PointerInput(interaction.POINTER_TOUCH, "touch"),
            )
            actions.w3c_actions.pointer_action.click_and_hold(element)
            actions.w3c_actions.pointer_action.pause(duration_ms / 1000)
            actions.w3c_actions.pointer_action.release()
            actions.perform()
        except Exception as exc:
            logger.debug(f"long_press failed: {exc}")

    def dismiss_keyboard(self, driver, platform_type: str) -> None:
        """
        Dismiss the on-screen keyboard.

        Args:
            driver: Appium WebDriver
            platform_type: "native_android" or "native_ios"
        """
        try:
            if platform_type == "native_ios":
                driver.execute_script("mobile: hideKeyboard")
            else:
                driver.hide_keyboard()
        except Exception as exc:
            logger.debug(f"dismiss_keyboard failed (may not be shown): {exc}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _android_scroll_down(self, driver, pixels: int) -> None:
        """W3C touch action scroll for Android."""
        try:
            size = driver.get_window_size()
            start_x = size["width"] // 2
            start_y = int(size["height"] * 0.7)
            end_y = max(0, start_y - pixels)
            self._w3c_swipe(driver, start_x, start_y, start_x, end_y, duration_ms=600)
        except Exception as exc:
            logger.debug(f"Android scroll_down failed: {exc}")

    def _ios_swipe_up(self, driver, pixels: int) -> None:
        """Swipe up (scroll down visually) on iOS via W3C actions."""
        try:
            size = driver.get_window_size()
            start_x = size["width"] // 2
            start_y = int(size["height"] * 0.7)
            end_y = max(0, start_y - pixels)
            self._w3c_swipe(driver, start_x, start_y, start_x, end_y, duration_ms=600)
        except Exception as exc:
            logger.debug(f"iOS swipe_up failed: {exc}")

    def _ios_edge_swipe_back(self, driver) -> None:
        """iOS left-edge swipe for back navigation."""
        try:
            size = driver.get_window_size()
            mid_y = size["height"] // 2
            self._w3c_swipe(driver, 5, mid_y, 300, mid_y, duration_ms=400)
        except Exception as exc:
            logger.debug(f"iOS edge swipe back failed: {exc}")

    def _w3c_swipe(
        self,
        driver,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration_ms: int = 600,
    ) -> None:
        """Generic W3C touch action swipe."""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.common.actions.action_builder import ActionBuilder
            from selenium.webdriver.common.actions.pointer_input import PointerInput
            from selenium.webdriver.common.actions import interaction

            actions = ActionChains(driver)
            actions.w3c_actions = ActionBuilder(
                driver,
                mouse=PointerInput(interaction.POINTER_TOUCH, "touch"),
            )
            actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pointer_action.pause(duration_ms / 1000)
            actions.w3c_actions.pointer_action.move_to_location(end_x, end_y)
            actions.w3c_actions.pointer_action.release()
            actions.perform()
        except Exception as exc:
            logger.debug(f"W3C swipe failed: {exc}")
