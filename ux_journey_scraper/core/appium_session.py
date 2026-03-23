"""
Appium session builder for Android (UiAutomator2) and iOS (XCUITest).

Validates the Appium server is reachable before starting a crawl.
"""
import logging
from typing import Dict

import requests

logger = logging.getLogger(__name__)

try:
    from appium import webdriver as appium_webdriver
    from appium.options.common.base import AppiumOptions
    _APPIUM_AVAILABLE = True
except ImportError:
    _APPIUM_AVAILABLE = False


class AppiumSession:
    """
    Builds and returns an Appium WebDriver for Android or iOS.

    Usage::

        session = AppiumSession()
        driver = session.create_driver(platform_config)
        # ... use driver ...
        driver.quit()
    """

    def create_driver(self, platform):
        """
        Create an Appium WebDriver for the given platform config.

        Args:
            platform: PlatformConfig with type in {"native_android", "native_ios"}
                      and a populated NativeAppConfig in platform.native

        Returns:
            Appium WebDriver instance

        Raises:
            RuntimeError: If Appium server is unreachable or Appium package not installed
        """
        if not _APPIUM_AVAILABLE:
            raise RuntimeError(
                "Appium-Python-Client is not installed. "
                "Install with: pip install 'ux-journey-scraper[native]'"
            )

        self._validate_server(platform.native.appium_server)

        if platform.type == "native_android":
            caps = self._android_caps(platform.native)
        else:
            caps = self._ios_caps(platform.native)

        logger.info(f"Connecting to Appium at {platform.native.appium_server} ({platform.type})")
        options = AppiumOptions()
        options.load_capabilities(caps)
        driver = appium_webdriver.Remote(
            command_executor=platform.native.appium_server,
            options=options,
        )
        logger.info("Appium session started")
        return driver

    def _android_caps(self, n) -> Dict:
        """Build UiAutomator2 capabilities for Android."""
        caps = {
            "platformName": "Android",
            "automationName": "UiAutomator2",
            "noReset": True,
            "uiautomator2ServerLaunchTimeout": 60000,
            "uiautomator2ServerInstallTimeout": 60000,
            "adbExecTimeout": 60000,
            "androidDeviceReadyTimeout": 60,
            "autoGrantPermissions": True,
            "chromedriverAutodownload": True,
        }
        if n.app_package:      caps["appPackage"] = n.app_package
        if n.app_activity:     caps["appActivity"] = n.app_activity
        if n.apk_path:         caps["app"] = n.apk_path
        if n.avd_name:         caps["avd"] = n.avd_name
        if n.device_name:      caps["deviceName"] = n.device_name
        if n.platform_version: caps["platformVersion"] = n.platform_version
        if n.extra_caps:       caps.update(n.extra_caps)
        return caps

    def _ios_caps(self, n) -> Dict:
        """Build XCUITest capabilities for iOS."""
        caps = {
            "platformName": "iOS",
            "automationName": "XCUITest",
            "noReset": True,
        }
        if n.bundle_id:          caps["bundleId"] = n.bundle_id
        if n.ipa_path:           caps["app"] = n.ipa_path
        if n.simulator_udid:     caps["udid"] = n.simulator_udid
        if n.device_name:        caps["deviceName"] = n.device_name
        if n.platform_version:   caps["platformVersion"] = n.platform_version
        if n.safari_initial_url: caps["safariInitialUrl"] = n.safari_initial_url
        if n.extra_caps:         caps.update(n.extra_caps)
        return caps

    def _validate_server(self, url: str) -> None:
        """
        Verify Appium server is reachable at the given URL.

        Args:
            url: Appium server base URL (e.g. "http://localhost:4723")

        Raises:
            RuntimeError: If the server is not reachable or returns an error status
        """
        status_url = f"{url.rstrip('/')}/status"
        try:
            resp = requests.get(status_url, timeout=5)
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Appium server at {url}. "
                "Start Appium with: appium --port 4723"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Appium server at {url} did not respond within 5 seconds."
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Appium server returned error: {e}")
        logger.debug(f"Appium server reachable at {url}")
