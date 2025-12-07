from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver

from core.configuration.configuration import Configuration
from core.logging.logging import Logger


class BrowserProvider(ABC):
    """
   Abstract provider: subclass implements build_option() and create_local_driver()
   Base class handles create_driver() logic (local vs remote) and settings (headless,size,maximize) to avoid duplication.
   """

    name: Optional[str] = None
    aliases: List[str] = []

    def __init__(self, config: Configuration):
        self.config = config

    @abstractmethod
    def build_options(self) -> Any:
        """Return browser-specific Options instance (ChromeOptions/FirefoxOptions/EdgeOptions)."""
        raise NotImplementedError

    def create_driver(self) -> WebDriver:
        """Initialize driver: apply common settings and select local/remote mode"""
        Logger.info("Creating WebDriver instance...")
        options = self.build_options()

        self._apply_common_settings(options)
        self._apply_overrides_from_json(options)

        remote_url = self.config.remote_url
        if remote_url:
            return self.create_remote_driver(options, remote_url)

        Logger.info(f"Using remote URL: {remote_url}" if remote_url else "Using local driver.")
        return self.create_local_driver(options)

    @abstractmethod
    def create_local_driver(self, options: Any) -> WebDriver:
        """Instantiate a local WebDriver using options and service."""
        Logger.info("Creating local WebDriver instance...")
        raise NotImplementedError

    def create_remote_driver(self, options: Any, remote_url: str) -> WebDriver:
        """Default remote creation uses webdriver.Remote(options=options)."""
        Logger.info(f"Creating remote WebDriver with URL: {remote_url}")
        return webdriver.Remote(command_executor=remote_url, options=options)

    # ================================
    #         COMMON SETTINGS
    # ================================

    def _apply_common_settings(self, options: Any):
        Logger.info("Applying common browser settings...")

        if self.config.headless:
            Logger.info(f"Headless mode: {self.config.headless}")
            self._add_headless(options)

            self._add_args(options, f"--window-size={self.config.window_width},{self.config.window_height}")
            Logger.info(f"Window size: {self.config.window_width}x{self.config.window_height}")

        else:
            if self.config.maximize:
                self._add_args(options, "--start-maximized")
                Logger.info("Start maximized")
            else:
                self._add_args(options, f"--window-size={self.config.window_width},{self.config.window_height}")
                Logger.info(f"Window size: {self.config.window_width}x{self.config.window_height}")

    # ================================
    #         HELPER HOOKS
    # ================================

    def _add_headless(self, options: Any) -> None:
        """Default: Chromium flag (Firefox subclass can override)."""
        try:
            options.add_argument("--headless=new")
        except Exception as e:
            Logger.warning(f"Could not apply headless argument: {e}")

    def _add_args(self, options: Any, *args: str) -> None:
        try:
            for a in args:
                options.add_argument(a)
        except Exception as e:
            Logger.warning(f"Could not apply arguments {args}: {e}")

    def _set_chromium_prefs(self, options: Any, prefs: Dict) -> None:
        """Default Chrome-style prefs; subclass Firefox override if needed."""
        try:
            options.add_experimental_option("prefs", prefs)
        except Exception as e:
            Logger.warning(f"Could not apply arguments {args}: {e}")

    def _set_capabilities(self, options: Any, caps: dict) -> None:
        for k, v in (caps or {}).items():
            options.set_capability(k, v)

    # ================================
    #         JSON OVERRIDES
    # ================================

    def _apply_overrides_from_json(self, options: Any) -> None:
        """
        Get data from Configuration (cached JSON):
        - global capabilities
        - block by browser: args/prefs/capabilities
        - authorize vendor keys to subclass
        """
        block = self.config.json_browser_block(self.config.browser)

        Logger.info("Applying overrides from JSON configuration...")

        # per-browser block (args/prefs/caps)
        if isinstance(block, dict):
            for a in (block.get("args") or []):
                try:
                    options.add_argument(str(a))
                except Exception as e:
                    Logger.warning(f"Could not apply browser arg {a}: {e}")

        prefs = block.get("prefs")
        if isinstance(prefs, dict):
            try:
                options.add_experimental_option("prefs", prefs)
            except Exception as e:
                Logger.warning(f"Could not apply browser prefs: {e}")

        caps = block.get("capabilities")
        if isinstance(caps, dict):
            for k, v in caps.items():
                try:
                    options.set_capability(k, v)
                except Exception as e:
                    Logger.warning(f"Could not set browser capability {k}: {e}")

        # vendor keys: goog:chromeOptions / ms:edgeOptions / moz:firefoxOptions
        self._apply_vendor_json(options, block)

    def _apply_vendor_json(self, options: Any, block: dict) -> None:
        """Subclasses handle vendor keys from block"""

