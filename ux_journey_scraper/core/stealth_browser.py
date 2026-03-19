"""
Stealth browser configuration for anti-bot detection bypass.

Implements comprehensive anti-detection measures:
- Remove webdriver flags
- Spoof user agent
- Randomize canvas fingerprint
- Set timezone/locale
- Inject anti-detection scripts
"""
import logging
from typing import Optional

from playwright.async_api import Browser, BrowserContext, async_playwright

from ux_journey_scraper.config.scrape_config import PlatformConfig

logger = logging.getLogger(__name__)


class StealthBrowser:
    """Manages stealth browser instances."""

    # Full anti-detection script
    ANTI_DETECTION_SCRIPT = """
    // Remove webdriver flag
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });

    // Add chrome object
    window.chrome = {
        runtime: {},
        loadTimes: function() {},
        csi: function() {},
        app: {}
    };

    // Mock plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {
                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf"},
                description: "Portable Document Format",
                filename: "internal-pdf-viewer",
                length: 1,
                name: "Chrome PDF Plugin"
            },
            {
                0: {type: "application/pdf", suffixes: "pdf"},
                description: "Portable Document Format",
                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                length: 1,
                name: "Chrome PDF Viewer"
            },
            {
                0: {type: "application/x-nacl", suffixes: ""},
                description: "Native Client Executable",
                filename: "internal-nacl-plugin",
                length: 2,
                name: "Native Client"
            }
        ]
    });

    // Mock languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en', 'hi-IN', 'hi']
    });

    // Override permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({state: Notification.permission}) :
            originalQuery(parameters)
    );

    // Mock battery
    if (navigator.getBattery) {
        navigator.getBattery = () => Promise.resolve({
            charging: true,
            chargingTime: 0,
            dischargingTime: Infinity,
            level: 1
        });
    }

    // Randomize canvas fingerprint slightly
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        const canvas = this;
        const ctx = canvas.getContext('2d');
        if (ctx) {
            const originalData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            // Add minimal noise
            for (let i = 0; i < originalData.data.length; i += 4) {
                if (Math.random() < 0.001) {
                    originalData.data[i] = (originalData.data[i] + Math.floor(Math.random() * 5)) % 256;
                }
            }
            ctx.putImageData(originalData, 0, 0);
        }
        return originalToDataURL.apply(this, arguments);
    };

    // Mock connection
    Object.defineProperty(navigator, 'connection', {
        get: () => ({
            effectiveType: '4g',
            rtt: 50,
            downlink: 10,
            saveData: false
        })
    });

    // Override toString
    const originalToString = Function.prototype.toString;
    Function.prototype.toString = function() {
        if (this === navigator.permissions.query) {
            return 'function query() { [native code] }';
        }
        return originalToString.apply(this, arguments);
    };
    """

    @staticmethod
    async def launch(
        platform_config: PlatformConfig,
        headless: bool = False,
        slow_mo: int = 0,
    ) -> tuple[Browser, BrowserContext]:
        """
        Launch a stealth browser with anti-detection measures.

        Args:
            platform_config: Platform configuration (viewport, user_agent, etc.)
            headless: Run in headless mode (visible = harder to detect)
            slow_mo: Slow down operations (ms)

        Returns:
            Tuple of (browser, context)
        """
        logger.info(f"Launching stealth browser: {platform_config.type}")

        # Try to use patchright (preferred), fall back to playwright
        try:
            from patchright.async_api import async_playwright as async_patchright

            p = await async_patchright().start()
            logger.debug("Using patchright (best anti-detection)")
        except ImportError:
            logger.debug("patchright not available, using standard playwright")
            p = await async_playwright().start()

        # Launch browser with anti-detection args
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )

        # Determine user agent
        user_agent = platform_config.user_agent
        if not user_agent:
            user_agent = StealthBrowser._get_default_user_agent(platform_config.type)

        # Create context with stealth settings
        context = await browser.new_context(
            viewport=platform_config.viewport,
            user_agent=user_agent,
            locale=platform_config.locale,
            timezone_id=platform_config.timezone_id,
            # Permissions
            permissions=["geolocation", "notifications"],
            # Extra HTTP headers
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Upgrade-Insecure-Requests": "1",
            },
        )

        # Inject anti-detection script into all pages
        await context.add_init_script(StealthBrowser.ANTI_DETECTION_SCRIPT)

        logger.info("Stealth browser ready")
        return browser, context

    @staticmethod
    def _get_default_user_agent(platform_type: str) -> str:
        """
        Get default user agent for platform type.

        Args:
            platform_type: "web_desktop", "web_mobile", or "web_tablet"

        Returns:
            User agent string
        """
        if platform_type == "web_mobile":
            return (
                "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Mobile Safari/537.36"
            )
        elif platform_type == "web_tablet":
            return (
                "Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/14.1.2 Mobile/15E148 Safari/604.1"
            )
        else:  # web_desktop
            return (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )

    @staticmethod
    async def configure_page(context: BrowserContext):
        """
        Configure additional page-level stealth settings.

        Args:
            context: Browser context
        """
        # Can add page-specific configurations here
        pass
