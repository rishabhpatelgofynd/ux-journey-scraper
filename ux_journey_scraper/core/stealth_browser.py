"""
Browser provider abstraction.
Local (Patchright) or cloud (Browserbase) — same API downstream.

Public API:
    create_stealth_browser(config, proxy_override) → (pw, browser, context)

Every module calls this — never create browsers directly.
"""
import os
import logging
from typing import Optional, Tuple, Dict

from playwright.async_api import Playwright, Browser, BrowserContext

from ..config.scrape_config import ScrapeConfig, PlatformConfig, BrowserProvider

logger = logging.getLogger(__name__)


# Full anti-detection script injected into every local browser page
FULL_SPOOF_SCRIPT = """
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


# Launch args — every local browser uses exactly these
# Never remove AutomationControlled — most important flag
LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-extensions",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--use-gl=desktop",
    "--enable-webgl",
    "--disable-dev-shm-usage",
    "--disable-automation",
    "--start-maximized",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-http2",  # Avoids ERR_HTTP2_PROTOCOL_ERROR on some networks
]


async def create_stealth_browser(
    config: ScrapeConfig,
    platform: Optional[PlatformConfig] = None,
    proxy_override: Optional[Dict[str, str]] = None,
) -> Tuple[Playwright, Browser, BrowserContext]:
    """
    Create a stealth browser session.
    Routes to local (Patchright) or cloud (Browserbase) based on config.

    Returns (playwright_instance, browser, context).
    Caller must close all three in reverse order.

    Args:
        config: Full scrape config
        platform: Which platform to emulate (viewport + UA).
                  If None, uses first platform in config.platforms.
        proxy_override: Override proxy settings (from ProxyRotator).
                        Only used in local mode — Browserbase handles its own proxies.
    """
    plat = platform or config.platforms[0]

    if config.browser.type == "browserbase":
        return await _create_browserbase(config.browser, plat)
    else:
        return await _create_local_patchright(config, plat, proxy_override)


# ──────────────────────────────────────────────────
# LOCAL PROVIDER (Patchright)
# ──────────────────────────────────────────────────

async def _create_local_patchright(
    config: ScrapeConfig,
    platform: PlatformConfig,
    proxy_override: Optional[Dict[str, str]],
) -> Tuple[Playwright, Browser, BrowserContext]:
    """
    Local Patchright browser.
    Handles: TLS fingerprint (via Patchright), JS spoofing (via FULL_SPOOF_SCRIPT),
    proxy (from config or override), viewport + UA (from platform).
    """
    # Try patchright first, fall back to playwright
    try:
        from patchright.async_api import async_playwright as async_patchright
        pw = await async_patchright().start()
        logger.debug("Using patchright (enhanced anti-detection)")
    except ImportError:
        logger.debug("patchright not available, using standard playwright")
        from playwright.async_api import async_playwright
        pw = await async_playwright().start()

    # Proxy: override > config > None
    proxy_settings = proxy_override
    if not proxy_settings and config.proxy.enabled:
        endpoint = os.environ.get(config.proxy.endpoint_env or "", "")
        if endpoint:
            proxy_settings = {"server": endpoint}

    browser = await pw.chromium.launch(
        headless=config.crawler.headless,
        args=LAUNCH_ARGS,
        proxy=proxy_settings,
    )

    context = await browser.new_context(
        viewport={
            "width": platform.viewport["width"],
            "height": platform.viewport["height"],
        },
        user_agent=platform.user_agent or _default_ua(platform.type),
        locale=platform.locale,
        timezone_id=platform.timezone_id,
        permissions=["geolocation"],
        java_script_enabled=True,
        has_touch=platform.type in ("web_mobile", "web_tablet"),
        is_mobile=platform.type == "web_mobile",
        device_scale_factor=2.0 if platform.type in ("web_mobile", "web_tablet") else 1.0,
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
        },
    )

    # Inject full JS spoof to every page
    await context.add_init_script(FULL_SPOOF_SCRIPT)

    logger.info(
        f"Local browser created: {platform.type} "
        f"({platform.viewport['width']}x{platform.viewport['height']}) "
        f"proxy={'yes' if proxy_settings else 'no'}"
    )

    return pw, browser, context


# ──────────────────────────────────────────────────
# CLOUD PROVIDER (Browserbase)
# ──────────────────────────────────────────────────

async def _create_browserbase(
    bb_config: BrowserProvider,
    platform: PlatformConfig,
) -> Tuple[Playwright, Browser, BrowserContext]:
    """
    Browserbase cloud browser.
    Handles: anti-detection, proxies, CAPTCHA solving, fingerprinting.
    We only need to set viewport + UA. Browserbase handles the rest.

    Requires: pip install browserbase
    Env vars: BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID
    """
    from playwright.async_api import async_playwright

    try:
        from browserbase import Browserbase
    except ImportError:
        raise ImportError(
            "browserbase package required for cloud browser. "
            "Install with: pip install browserbase"
        )

    api_key = os.environ.get(bb_config.api_key_env, "")
    project_id = os.environ.get(bb_config.project_id_env, "")

    if not api_key:
        raise ValueError(
            f"Browserbase API key not found in env var: {bb_config.api_key_env}"
        )
    if not project_id:
        raise ValueError(
            f"Browserbase project ID not found in env var: {bb_config.project_id_env}"
        )

    bb = Browserbase(api_key=api_key)

    # Build session creation params
    session_params = {
        "project_id": project_id,
        "browser_settings": {
            "viewport": {
                "width": platform.viewport["width"],
                "height": platform.viewport["height"],
            },
            "fingerprint": {
                "browsers": ["chrome"],
                "devices": ["mobile"] if platform.type == "web_mobile" else ["desktop"],
                "operating_systems": (
                    ["ios"] if platform.type == "web_mobile" else ["windows", "macos"]
                ),
                "screen": {
                    "min_width": platform.viewport["width"],
                    "max_width": platform.viewport["width"],
                    "min_height": platform.viewport["height"],
                    "max_height": platform.viewport["height"],
                },
            },
        },
    }

    # Proxy configuration
    if bb_config.use_proxy:
        proxy_config = {"type": "browserbase"}
        if bb_config.proxy_geo:
            proxy_config["geolocation"] = {"country": bb_config.proxy_geo}
        session_params["proxies"] = [proxy_config]

    # Context persistence (cookies across sessions)
    if bb_config.context_id:
        session_params["browser_settings"]["context"] = {
            "id": bb_config.context_id,
            "persist": True,
        }

    # Keep alive
    if bb_config.keep_alive:
        session_params["keep_alive"] = True

    # Create Browserbase session
    session = bb.sessions.create(**session_params)
    connect_url = session.connect_url

    logger.info(
        f"Browserbase session created: {session.id} "
        f"({platform.type} {platform.viewport['width']}x{platform.viewport['height']})"
    )

    # Connect via Playwright CDP
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(connect_url)

    # Browserbase provides the context — get it from the connected browser
    context = browser.contexts[0]

    # Set user agent if Browserbase didn't set it from fingerprint
    # (Browserbase fingerprint usually handles this, but override for safety)
    if platform.user_agent:
        await context.set_extra_http_headers({
            "User-Agent": platform.user_agent,
        })

    logger.info(f"Connected to Browserbase session: {session.id}")

    return pw, browser, context


# ──────────────────────────────────────────────────
# SHARED UTILS
# ──────────────────────────────────────────────────

def _default_ua(platform_type: str) -> str:
    """Default user agents per platform type."""
    uas = {
        "web_desktop": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "web_mobile": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.4.1 Mobile/15E148 Safari/604.1"
        ),
        "web_tablet": (
            "Mozilla/5.0 (iPad; CPU OS 17_4_1 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.4.1 Mobile/15E148 Safari/604.1"
        ),
    }
    return uas.get(platform_type, uas["web_desktop"])
