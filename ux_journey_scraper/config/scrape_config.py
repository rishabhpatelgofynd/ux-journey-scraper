"""
YAML-based configuration system for autonomous crawling.

Supports multi-platform, multi-auth scenarios with comprehensive form filling.
"""
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PlatformConfig:
    """Configuration for a specific platform (desktop, mobile, tablet)."""

    type: str  # "web_desktop", "web_mobile", "web_tablet"
    viewport: Dict[str, int]  # {"width": 1920, "height": 1080}
    user_agent: Optional[str] = None
    locale: str = "en-IN"
    timezone_id: str = "Asia/Kolkata"

    def __post_init__(self):
        """Validate platform configuration."""
        valid_types = ["web_desktop", "web_mobile", "web_tablet"]
        if self.type not in valid_types:
            raise ValueError(f"Invalid platform type: {self.type}. Must be one of {valid_types}")

        required_keys = {"width", "height"}
        if not required_keys.issubset(self.viewport.keys()):
            raise ValueError(f"Viewport must contain {required_keys}")

        if self.viewport["width"] <= 0 or self.viewport["height"] <= 0:
            raise ValueError("Viewport dimensions must be positive")


@dataclass
class AuthConfig:
    """Authentication configuration."""

    logged_out: bool = True
    logged_in: bool = False
    credentials: Optional[Dict[str, str]] = None  # {"username": "...", "password": "..."}
    login_url: Optional[str] = None
    login_success_indicator: Optional[str] = None  # CSS selector or URL fragment
    session_file: Optional[str] = None  # Path to save/load session

    def __post_init__(self):
        """Validate auth configuration."""
        if self.logged_in and not self.credentials:
            if not self.session_file:
                raise ValueError(
                    "logged_in=true requires either credentials or session_file"
                )

        if self.logged_in and not self.login_success_indicator:
            raise ValueError(
                "logged_in=true requires login_success_indicator to verify auth"
            )


@dataclass
class FormFillConfig:
    """Smart form filling configuration (autocomplete-based)."""

    # Personal info
    first_name: str = "Test"
    last_name: str = "User"
    email: str = "testuser@example.com"
    phone: str = "+91 98765 43210"

    # Address
    address_line1: str = "123 Test Street"
    address_line2: str = "Apartment 4B"
    city: str = "Mumbai"
    state: str = "Maharashtra"
    postal_code: str = "400001"
    country: str = "IN"

    # Payment (test cards only)
    card_number: str = "4111111111111111"  # Visa test card
    card_expiry_month: str = "12"
    card_expiry_year: str = "2025"
    card_cvv: str = "123"
    card_name: str = "Test User"

    # Company info
    organization: str = "Test Company"
    job_title: str = "QA Engineer"

    # Extra fields
    birthday_day: str = "15"
    birthday_month: str = "06"
    birthday_year: str = "1990"

    def __post_init__(self):
        """Validate form fill configuration."""
        # Ensure test card (never real payment)
        valid_test_cards = [
            "4111111111111111",  # Visa
            "5555555555554444",  # Mastercard
            "378282246310005",   # Amex
        ]
        if self.card_number not in valid_test_cards:
            raise ValueError(
                f"Only test cards allowed: {valid_test_cards}. "
                f"Never use real payment details."
            )


@dataclass
class SessionStrategy:
    """Controls how the crawl is split across multiple browser sessions."""

    mode: str = "split"
    # "split" = multiple visit sessions with cooldowns (default, recommended)
    # "continuous" = original behavior, all pages in one session (for weak-defense sites)

    pages_per_session: int = 20            # Max pages per visit session
    min_cooldown_sec: int = 120            # 2 min minimum between sessions
    max_cooldown_sec: int = 600            # 10 min maximum between sessions
    persist_cookies: bool = True           # Reuse cookies across sessions (returning visitor)
    randomize_entry_points: bool = True    # Don't always start from homepage
    rotate_ip_per_session: bool = False    # Rotate proxy IP every session
    rotate_ip_per_n_sessions: int = 3      # Rotate every N sessions (if above is False)

    def __post_init__(self):
        """Validate session strategy configuration."""
        valid_modes = ["split", "continuous"]
        if self.mode not in valid_modes:
            raise ValueError(f"Invalid session mode: {self.mode}. Must be one of {valid_modes}")

        if self.pages_per_session < 1:
            raise ValueError("pages_per_session must be at least 1")
        if self.min_cooldown_sec < 0:
            raise ValueError("min_cooldown_sec must be non-negative")
        if self.max_cooldown_sec < self.min_cooldown_sec:
            raise ValueError("max_cooldown_sec must be >= min_cooldown_sec")
        if self.rotate_ip_per_n_sessions < 1:
            raise ValueError("rotate_ip_per_n_sessions must be at least 1")


@dataclass
class ProxySettings:
    """Proxy configuration for IP rotation and anonymization."""

    enabled: bool = False
    provider: str = "residential"          # residential | datacenter | rotating
    endpoint_env: Optional[str] = None     # Env var holding proxy URL
    rotate_per: str = "session"            # session | request | domain
    pool_size: int = 5                     # Number of IPs in rotation pool
    geo: Optional[str] = None              # Geo target: "IN", "US", etc.
    domains: List[str] = field(default_factory=list)  # Domain filter

    def __post_init__(self):
        """Validate proxy configuration."""
        valid_providers = ["residential", "datacenter", "rotating"]
        if self.provider not in valid_providers:
            raise ValueError(f"Invalid provider: {self.provider}. Must be one of {valid_providers}")

        valid_rotate_per = ["session", "request", "domain"]
        if self.rotate_per not in valid_rotate_per:
            raise ValueError(f"Invalid rotate_per: {self.rotate_per}. Must be one of {valid_rotate_per}")

        if self.pool_size < 1:
            raise ValueError("pool_size must be at least 1")


@dataclass
class BrowserProvider:
    """Browser backend configuration (local Patchright or cloud Browserbase)."""

    type: str = "local"
    # "local" = Patchright on local machine (default, free)
    # "browserbase" = Browserbase cloud browser (paid, managed anti-detection)

    # Browserbase-specific settings (ignored when type = "local")
    api_key_env: str = "BROWSERBASE_API_KEY"        # Env var for API key
    project_id_env: str = "BROWSERBASE_PROJECT_ID"  # Env var for project ID
    use_proxy: bool = True                           # Use Browserbase's proxy network
    proxy_geo: Optional[str] = None                  # Geo target: "IN", "US", etc.
    use_stealth: bool = True                         # Enable Browserbase stealth mode
    solve_captchas: bool = True                      # Enable managed CAPTCHA solving
    keep_alive: bool = False                         # Keep session alive after disconnect
    context_id: Optional[str] = None                 # Browserbase Context ID for cookie persistence

    def __post_init__(self):
        """Validate browser provider configuration."""
        valid_types = ["local", "browserbase"]
        if self.type not in valid_types:
            raise ValueError(f"Invalid browser type: {self.type}. Must be one of {valid_types}")


@dataclass
class CrawlerConfig:
    """Crawler behavior configuration."""

    max_depth: int = 8  # Maximum click depth from seed URLs
    max_pages: int = 200  # Maximum screens to capture
    delay_ms: int = 800  # Base delay between actions (ms)
    delay_jitter_ms: int = 400  # Random jitter added to delay (ms)
    timeout_per_page_ms: int = 15000  # Max wait per page (ms)
    max_retries: int = 2  # Retries on page load failure
    respect_robots: bool = True  # Check robots.txt
    follow_external_links: bool = False  # Stay within base_url domain
    headless: bool = True  # Run browser in headless mode

    def __post_init__(self):
        """Validate crawler configuration."""
        if self.max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        if self.max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        if self.delay_ms < 0:
            raise ValueError("delay_ms must be non-negative")
        if self.timeout_per_page_ms < 1000:
            raise ValueError("timeout_per_page_ms must be at least 1000ms")


@dataclass
class ScrapeConfig:
    """Main scrape configuration loaded from YAML."""

    target: Dict[str, str]  # {"name": "Example", "base_url": "https://example.com"}
    platforms: List[PlatformConfig]
    auth: AuthConfig
    seed_urls: List[str]
    form_fill: FormFillConfig = field(default_factory=FormFillConfig)
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    session_strategy: SessionStrategy = field(default_factory=SessionStrategy)
    proxy: ProxySettings = field(default_factory=ProxySettings)
    browser: BrowserProvider = field(default_factory=BrowserProvider)

    # Runtime fields (not from YAML)
    run_id: Optional[str] = None
    output_dir: str = "context"
    base_url: Optional[str] = None  # Derived from target
    post_order: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate main configuration."""
        # Validate target
        required_target_keys = {"name", "base_url"}
        if not required_target_keys.issubset(self.target.keys()):
            raise ValueError(f"target must contain {required_target_keys}")

        if not self.target["base_url"].startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")

        # Set base_url from target
        if self.base_url is None:
            self.base_url = self.target["base_url"]

        # Validate platforms
        if not self.platforms:
            raise ValueError("At least one platform configuration required")

        # Validate seed URLs
        if not self.seed_urls:
            raise ValueError("At least one seed URL required")

        for url in self.seed_urls:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid seed URL: {url}")

        # Initialize post_order if not set
        if self.post_order is None:
            self.post_order = {"seeds": []}

    @classmethod
    def load(cls, config_path: str) -> "ScrapeConfig":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML config file

        Returns:
            ScrapeConfig: Parsed and validated configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
            yaml.YAMLError: If YAML parsing fails
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Empty config file: {config_path}")

        # Parse target
        target = data.get("target", {})

        # Parse platforms
        platforms_data = data.get("platforms", [])
        platforms = [
            PlatformConfig(
                type=p.get("type"),
                viewport=p.get("viewport", {}),
                user_agent=p.get("user_agent"),
                locale=p.get("locale", "en-IN"),
                timezone_id=p.get("timezone_id", "Asia/Kolkata"),
            )
            for p in platforms_data
        ]

        # Parse auth
        auth_data = data.get("auth", {})
        auth = AuthConfig(
            logged_out=auth_data.get("logged_out", True),
            logged_in=auth_data.get("logged_in", False),
            credentials=auth_data.get("credentials"),
            login_url=auth_data.get("login_url"),
            login_success_indicator=auth_data.get("login_success_indicator"),
            session_file=auth_data.get("session_file"),
        )

        # Parse seed URLs
        seed_urls = data.get("seed_urls", [])

        # Parse form fill
        form_fill_data = data.get("form_fill", {})
        form_fill = FormFillConfig(**form_fill_data) if form_fill_data else FormFillConfig()

        # Parse crawler
        crawler_data = data.get("crawler", {})
        crawler = CrawlerConfig(**crawler_data) if crawler_data else CrawlerConfig()

        # Parse session strategy
        session_data = data.get("session_strategy", {})
        session_strategy = SessionStrategy(**session_data) if session_data else SessionStrategy()

        # Parse proxy settings
        proxy_data = data.get("proxy", {})
        proxy = ProxySettings(**proxy_data) if proxy_data else ProxySettings()

        # Parse browser provider
        browser_data = data.get("browser", {})
        browser = BrowserProvider(**browser_data) if browser_data else BrowserProvider()

        # Parse runtime options
        run_id = data.get("run_id")
        output_dir = data.get("output_dir", "context")
        post_order = data.get("post_order", {"seeds": []})

        return cls(
            target=target,
            platforms=platforms,
            auth=auth,
            seed_urls=seed_urls,
            form_fill=form_fill,
            crawler=crawler,
            session_strategy=session_strategy,
            proxy=proxy,
            browser=browser,
            run_id=run_id,
            output_dir=output_dir,
            post_order=post_order,
        )

    def save(self, config_path: str) -> None:
        """
        Save configuration to YAML file.

        Args:
            config_path: Path to save YAML config
        """
        data = {
            "target": self.target,
            "platforms": [
                {
                    "type": p.type,
                    "viewport": p.viewport,
                    "user_agent": p.user_agent,
                    "locale": p.locale,
                    "timezone_id": p.timezone_id,
                }
                for p in self.platforms
            ],
            "auth": {
                "logged_out": self.auth.logged_out,
                "logged_in": self.auth.logged_in,
                "credentials": self.auth.credentials,
                "login_url": self.auth.login_url,
                "login_success_indicator": self.auth.login_success_indicator,
                "session_file": self.auth.session_file,
            },
            "seed_urls": self.seed_urls,
            "form_fill": {
                "first_name": self.form_fill.first_name,
                "last_name": self.form_fill.last_name,
                "email": self.form_fill.email,
                "phone": self.form_fill.phone,
                "address_line1": self.form_fill.address_line1,
                "address_line2": self.form_fill.address_line2,
                "city": self.form_fill.city,
                "state": self.form_fill.state,
                "postal_code": self.form_fill.postal_code,
                "country": self.form_fill.country,
                "card_number": self.form_fill.card_number,
                "card_expiry_month": self.form_fill.card_expiry_month,
                "card_expiry_year": self.form_fill.card_expiry_year,
                "card_cvv": self.form_fill.card_cvv,
                "card_name": self.form_fill.card_name,
                "organization": self.form_fill.organization,
                "job_title": self.form_fill.job_title,
                "birthday_day": self.form_fill.birthday_day,
                "birthday_month": self.form_fill.birthday_month,
                "birthday_year": self.form_fill.birthday_year,
            },
            "crawler": {
                "max_depth": self.crawler.max_depth,
                "max_pages": self.crawler.max_pages,
                "delay_ms": self.crawler.delay_ms,
                "delay_jitter_ms": self.crawler.delay_jitter_ms,
                "timeout_per_page_ms": self.crawler.timeout_per_page_ms,
                "max_retries": self.crawler.max_retries,
                "respect_robots": self.crawler.respect_robots,
                "follow_external_links": self.crawler.follow_external_links,
                "headless": self.crawler.headless,
            },
            "session_strategy": {
                "mode": self.session_strategy.mode,
                "pages_per_session": self.session_strategy.pages_per_session,
                "min_cooldown_sec": self.session_strategy.min_cooldown_sec,
                "max_cooldown_sec": self.session_strategy.max_cooldown_sec,
                "persist_cookies": self.session_strategy.persist_cookies,
                "randomize_entry_points": self.session_strategy.randomize_entry_points,
                "rotate_ip_per_session": self.session_strategy.rotate_ip_per_session,
                "rotate_ip_per_n_sessions": self.session_strategy.rotate_ip_per_n_sessions,
            },
            "proxy": {
                "enabled": self.proxy.enabled,
                "provider": self.proxy.provider,
                "endpoint_env": self.proxy.endpoint_env,
                "rotate_per": self.proxy.rotate_per,
                "pool_size": self.proxy.pool_size,
                "geo": self.proxy.geo,
                "domains": self.proxy.domains,
            },
            "browser": {
                "type": self.browser.type,
                "api_key_env": self.browser.api_key_env,
                "project_id_env": self.browser.project_id_env,
                "use_proxy": self.browser.use_proxy,
                "proxy_geo": self.browser.proxy_geo,
                "use_stealth": self.browser.use_stealth,
                "solve_captchas": self.browser.solve_captchas,
                "keep_alive": self.browser.keep_alive,
                "context_id": self.browser.context_id,
            },
        }

        if self.run_id:
            data["run_id"] = self.run_id
        if self.output_dir != "context":
            data["output_dir"] = self.output_dir
        if self.post_order and self.post_order.get("seeds"):
            data["post_order"] = self.post_order

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
