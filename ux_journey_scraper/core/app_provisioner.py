"""
App Provisioner — automatically discovers, downloads, and installs
mobile apps for native testing.

Usage:
    provisioner = AppProvisioner()
    config = await provisioner.provision("Amazon", "native_android")
    # Returns ready NativeAppConfig — pass directly to AppiumCrawler
"""
import asyncio
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Well-known brand → package/bundle mapping (instant, no API call)
KNOWN_ANDROID = {
    "amazon":     ("com.amazon.mShop.android.shopping", "com.amazon.mShop.home.HomeActivity"),
    "flipkart":   ("com.flipkart.android",              ".MainActivity"),
    "myntra":     ("com.myntra.android",                ".MainActivity"),
    "ajio":       ("com.ril.ajio",                      ".MainActivity"),
    "swiggy":     ("in.swiggy.android",                 ".MainActivity"),
    "zomato":     ("com.application.zomato",            ".MainActivity"),
    "meesho":     ("com.meesho.supply",                 ".MainActivity"),
    "snapdeal":   ("com.snapdeal.main",                 ".MainActivity"),
    "nykaa":      ("com.fsn.nykaa",                     ".MainActivity"),
    "walmart":    ("com.walmart.android",               ".app.MainActivityProxy"),
    "target":     ("com.target.ui",                     ".MainActivity"),
    "ebay":       ("com.ebay.mobile",                   ".MainActivity"),
    "etsy":       ("com.etsy.android",                  ".MainActivity"),
    "shein":      ("com.zzkko",                         ".MainActivity"),
    "temu":       ("com.einnovation.temu",              ".MainActivity"),
}

KNOWN_IOS = {
    "amazon":   "com.amazon.Amazon",
    "flipkart": "com.flipkart.iphone",
    "myntra":   "com.myntra.MyntraApp",
    "swiggy":   "in.swiggy.SwiggyApp",
    "zomato":   "com.zomato.Zomato",
    "walmart":  "com.walmart.customer",
    "target":   "com.target.mobile",
    "ebay":     "com.ebay.iphone",
    "etsy":     "com.etsy.etsyforios",
}

APK_CACHE_DIR = Path.home() / ".ux-journey-scraper" / "apks"


class AppProvisioner:
    """
    Automatically provisions mobile apps for native testing.

    Handles the full pipeline:
    1. Discover package name from brand name
    2. Check if a device/emulator is connected — start one if not
    3. Check if the app is already installed
    4. Download the APK if needed
    5. Install the APK
    6. Return a ready NativeAppConfig
    """

    def __init__(self):
        sdk = Path.home() / "Library" / "Android" / "sdk"
        self._adb = str(sdk / "platform-tools" / "adb")
        self._emulator = str(sdk / "emulator" / "emulator")
        APK_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def provision(self, brand_name: str, platform_type: str,
                        appium_server: str = "http://localhost:4723"):
        """
        Full auto-provisioning pipeline.

        Args:
            brand_name:     e.g. "Amazon", "Flipkart"
            platform_type:  "native_android" or "native_ios"
            appium_server:  Appium server URL

        Returns:
            NativeAppConfig ready to pass to AppiumCrawler / PlatformConfig
        """
        from ux_journey_scraper.config.scrape_config import NativeAppConfig

        brand = brand_name.lower().strip()
        logger.info(f"Provisioning {brand} for {platform_type}")

        if platform_type == "native_android":
            return await self._provision_android(brand, appium_server)
        elif platform_type == "native_ios":
            return await self._provision_ios(brand, appium_server)
        else:
            raise ValueError(f"Unsupported platform: {platform_type}")

    # ------------------------------------------------------------------
    # Android provisioning
    # ------------------------------------------------------------------

    async def _provision_android(self, brand: str, appium_server: str):
        from ux_journey_scraper.config.scrape_config import NativeAppConfig

        # 1. Discover package name
        package, activity = self._discover_android_package(brand)
        logger.info(f"Android package: {package}")

        # 2. Ensure emulator is running
        click_log("Checking Android device...")
        await self._ensure_android_device()
        click_log("Device ready.")

        # 2b. Ensure Appium is running
        await self._ensure_appium(appium_server)

        # 3. Check if already installed
        if self._is_installed_android(package):
            click_log(f"{brand.title()} already installed.")
        else:
            # 4. Download APK
            click_log(f"Downloading {brand.title()} APK...")
            apk_path = await self._download_apk(package, brand)
            # 5. Install with retry
            click_log(f"Installing {brand.title()}...")
            for attempt in range(3):
                try:
                    self._install_apk(apk_path)
                    click_log(f"{brand.title()} installed.")
                    break
                except RuntimeError as e:
                    if attempt < 2:
                        click_log(f"Install attempt {attempt+1} failed, retrying...")
                        await asyncio.sleep(3)
                    else:
                        # Last attempt — check if actually installed despite error
                        if self._is_installed_android(package):
                            click_log(f"{brand.title()} installed (despite error).")
                        else:
                            raise

        # 6. Always auto-detect real activity from device (overrides table)
        detected = self._detect_main_activity(package)
        if detected:
            activity = detected
            logger.info(f"Using detected activity: {activity}")

        return NativeAppConfig(
            appium_server=appium_server,
            app_package=package,
            app_activity=activity,
        )

    # ------------------------------------------------------------------
    # iOS provisioning
    # ------------------------------------------------------------------

    async def _provision_ios(self, brand: str, appium_server: str):
        from ux_journey_scraper.config.scrape_config import NativeAppConfig

        bundle_id = self._discover_ios_bundle(brand)
        logger.info(f"iOS bundle: {bundle_id}")

        # Detect booted simulator
        udid = self._booted_simulator_udid()
        if not udid:
            raise RuntimeError(
                "No iOS Simulator booted. Open Xcode → open Simulator, or run:\n"
                "  xcrun simctl boot <UDID>"
            )

        click_log(f"Using simulator: {udid}")

        return NativeAppConfig(
            appium_server=appium_server,
            bundle_id=bundle_id,
            simulator_udid=udid,
        )

    # ------------------------------------------------------------------
    # Device management
    # ------------------------------------------------------------------

    async def _ensure_appium(self, server_url: str):
        """Start Appium if not already running."""
        import requests as _req
        status_url = f"{server_url.rstrip('/')}/status"
        try:
            _req.get(status_url, timeout=3)
            click_log("Appium already running.")
            return
        except Exception:
            pass

        appium_bin = shutil.which("appium")
        if not appium_bin:
            raise RuntimeError(
                "Appium not found. Install with: npm install -g appium"
            )

        port = server_url.split(":")[-1].rstrip("/")
        click_log(f"Starting Appium on port {port}...")
        env = self._android_env()
        subprocess.Popen(
            [appium_bin, "--port", port],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait up to 15s for Appium to be ready
        for _ in range(15):
            await asyncio.sleep(1)
            try:
                _req.get(status_url, timeout=2)
                click_log("Appium started.")
                return
            except Exception:
                pass

        raise RuntimeError(f"Appium did not start within 15 seconds at {server_url}")

    async def _ensure_android_device(self):
        """Start the first available AVD if no device is connected."""
        if self._connected_device():
            return

        avds = self._list_avds()
        if not avds:
            raise RuntimeError(
                "No Android emulator running and no AVD found.\n"
                "Create an AVD in Android Studio → Virtual Device Manager."
            )

        avd = avds[0]
        click_log(f"Starting emulator: {avd}")
        env = self._android_env()
        subprocess.Popen(
            [self._emulator, "-avd", avd, "-dns-server", "8.8.8.8",
             "-no-snapshot-save", "-no-boot-anim"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait for adb to see the device
        subprocess.run([self._adb, "wait-for-device"], env=env, timeout=120)

        # Wait for full boot
        click_log("Waiting for emulator to fully boot...")
        for _ in range(60):
            result = subprocess.run(
                [self._adb, "shell", "getprop", "sys.boot_completed"],
                capture_output=True, text=True, env=env,
            )
            if result.stdout.strip() == "1":
                await asyncio.sleep(2)  # Extra settle time
                return
            await asyncio.sleep(3)

        raise RuntimeError("Emulator did not fully boot within 3 minutes.")

    def _connected_device(self) -> Optional[str]:
        """Return device serial if a device/emulator is connected."""
        result = subprocess.run(
            [self._adb, "devices"], capture_output=True, text=True,
            env=self._android_env(),
        )
        for line in result.stdout.splitlines()[1:]:
            if "\tdevice" in line:
                return line.split("\t")[0]
        return None

    def _list_avds(self):
        """List available AVDs."""
        result = subprocess.run(
            [self._emulator, "-list-avds"],
            capture_output=True, text=True, env=self._android_env(),
        )
        return [l.strip() for l in result.stdout.splitlines() if l.strip()]

    def _booted_simulator_udid(self) -> Optional[str]:
        """Return UDID of the first booted iOS simulator."""
        import shlex
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "booted", "--json"],
                capture_output=True, text=True,
            )
            import json
            data = json.loads(result.stdout)
            for runtime, devices in data.get("devices", {}).items():
                for d in devices:
                    if d.get("state") == "Booted":
                        return d["udid"]
        except Exception as e:
            logger.debug(f"Could not list iOS simulators: {e}")
        return None

    # ------------------------------------------------------------------
    # App check + install
    # ------------------------------------------------------------------

    def _is_installed_android(self, package: str) -> bool:
        result = subprocess.run(
            [self._adb, "shell", "pm", "list", "packages", package],
            capture_output=True, text=True, env=self._android_env(),
        )
        return package in result.stdout

    def _install_apk(self, apk_path: str):
        """Install APK or XAPK on the connected device."""
        if apk_path.endswith(".xapk") or apk_path.endswith(".apkm"):
            self._install_xapk(apk_path)
        else:
            result = subprocess.run(
                [self._adb, "install", "-r", "-t", apk_path],
                capture_output=True, text=True, env=self._android_env(),
                timeout=180,
            )
            if "Success" not in result.stdout and "Success" not in result.stderr:
                raise RuntimeError(
                    f"APK install failed: {result.stderr or result.stdout}"
                )

    def _install_xapk(self, xapk_path: str):
        """Extract and install an XAPK/APKM bundle using adb install-multiple."""
        import zipfile
        import tempfile

        extract_dir = Path(tempfile.mkdtemp(prefix="ux_xapk_"))
        try:
            click_log("Extracting XAPK bundle...")
            with zipfile.ZipFile(xapk_path, "r") as zf:
                zf.extractall(extract_dir)

            apk_files = list(extract_dir.glob("*.apk"))
            if not apk_files:
                raise RuntimeError(f"No APK files found inside {xapk_path}")

            click_log(f"Installing {len(apk_files)} APK split(s)...")
            cmd = [self._adb, "install-multiple", "-r", "-t"] + [str(f) for f in apk_files]
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                env=self._android_env(), timeout=300,
            )
            if "Success" not in result.stdout and "Success" not in result.stderr:
                raise RuntimeError(
                    f"XAPK install failed: {result.stderr or result.stdout}"
                )
        finally:
            import shutil as _shutil
            _shutil.rmtree(extract_dir, ignore_errors=True)

    def _detect_main_activity(self, package: str) -> Optional[str]:
        """Auto-detect the main launcher activity."""
        result = subprocess.run(
            [self._adb, "shell", "cmd", "package", "resolve-activity",
             "--brief", package],
            capture_output=True, text=True, env=self._android_env(),
        )
        for line in result.stdout.splitlines():
            if "/" in line and package in line:
                return line.split("/")[-1].strip()
        return None

    # ------------------------------------------------------------------
    # APK download
    # ------------------------------------------------------------------

    async def _download_apk(self, package: str, brand: str) -> str:
        """Try to download APK automatically, fall back to instructions."""
        # Check cache for any format
        for ext in (".apk", ".xapk", ".apkm"):
            cached = APK_CACHE_DIR / f"{package}{ext}"
            if cached.exists():
                click_log(f"Using cached APK: {cached}")
                return str(cached)

        # Try apkeep (most reliable CLI downloader)
        if shutil.which("apkeep"):
            try:
                return await self._download_via_apkeep(package, str(cached))
            except Exception as e:
                logger.debug(f"apkeep failed: {e}")

        # Manual fallback with clear instructions
        raise RuntimeError(
            f"\nCould not auto-download the {brand.title()} APK.\n\n"
            f"Manual steps (one time only):\n"
            f"  1. Go to apkpure.com and search '{brand.title()}'\n"
            f"  2. Download the APK (not XAPK) to your Mac\n"
            f"  3. Copy it to: {cached}\n"
            f"  4. Re-run — it will be cached for future runs\n\n"
            f"Or install apkeep for fully automatic downloads:\n"
            f"  brew install apkeep\n"
        )

    async def _download_via_apkeep(self, package: str, output_path: str) -> str:
        """Download APK/XAPK using apkeep CLI."""
        proc = await asyncio.create_subprocess_exec(
            "apkeep", "-a", package, "-d", "apk-pure", str(APK_CACHE_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        if proc.returncode != 0:
            raise RuntimeError(stderr.decode())

        # apkeep saves as {package}.apk or {package}.xapk
        for ext in (".apk", ".xapk", ".apkm"):
            candidate = APK_CACHE_DIR / f"{package}{ext}"
            if candidate.exists():
                return str(candidate)
        raise RuntimeError(
            f"apkeep finished but no APK found in {APK_CACHE_DIR}"
        )

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _discover_android_package(self, brand: str):
        """Return (package_name, activity) for a brand."""
        if brand in KNOWN_ANDROID:
            return KNOWN_ANDROID[brand]

        # Try google-play-scraper live search
        try:
            from google_play_scraper import search
            results = search(brand, n_hits=1, lang="en", country="in")
            if results:
                package = results[0]["appId"]
                logger.info(f"Found via Play Store search: {package}")
                return package, ".MainActivity"
        except Exception as e:
            logger.debug(f"Play Store search failed: {e}")

        raise ValueError(
            f"Could not find Android package for '{brand}'.\n"
            f"Add it to KNOWN_ANDROID in app_provisioner.py or specify "
            f"app_package directly in your config."
        )

    def _discover_ios_bundle(self, brand: str) -> str:
        """Return iOS bundle ID for a brand."""
        if brand in KNOWN_IOS:
            return KNOWN_IOS[brand]
        raise ValueError(
            f"Could not find iOS bundle ID for '{brand}'.\n"
            f"Add it to KNOWN_IOS in app_provisioner.py or specify "
            f"bundle_id directly in your config."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _android_env(self) -> dict:
        """Build environment dict with ANDROID_HOME set."""
        import os
        env = os.environ.copy()
        android_home = str(Path.home() / "Library" / "Android" / "sdk")
        env["ANDROID_HOME"] = android_home
        env["ANDROID_SDK_ROOT"] = android_home
        env["PATH"] = (
            f"{android_home}/platform-tools:"
            f"{android_home}/emulator:"
            f"{android_home}/tools:"
            + env.get("PATH", "")
        )
        return env


def click_log(msg: str):
    """Print a log message (uses click if available)."""
    try:
        import click
        click.echo(f"  {msg}")
    except ImportError:
        print(f"  {msg}")
