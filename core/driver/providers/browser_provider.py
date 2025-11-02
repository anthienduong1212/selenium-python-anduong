import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from selenium.webdriver.remote.webdriver import WebDriver
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
        Logger.debug(Logger.info(f"Using remote URL: {remote_url}" if remote_url else "Using local driver."))
        raise NotImplementedError

    def create_driver(self) -> WebDriver:
        """Initialize driver: apply common settings and select local/remote mode"""
        Logger.info("Creating WebDriver instance...")
        options = self.build_options()
        self.apply_common_settings(options)
        self.apply_vendor_overrides(options)

        remote_url = self.config.per_browser_remote_url.get(self.name) or self.config.remote_url
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
        from selenium import webdriver
        Logger.info(f"Creating remote WebDriver with URL: {remote_url}")
        return webdriver.Remote(command_executor=remote_url, options=options)

    # ================================
    #         HOOKS OVERRIDEABLE
    # ================================

    def apply_vendor_overrides(self, options: Any):
        """Subclasses can add args/prefs/caps of vendor from ENV/JSON"""
        return

    # ================================
    #         COMMON SETTINGS
    # ================================

    def apply_common_settings(self, options: Any):
        Logger.info("Applying common browser settings...")
        if self.config.headless:
            # keep browser-specific headless flag in subclass or here by convention
            Logger.info(f"Headless mode: {self.config.headless}")
            self._add_headless(options)

        if self.config.maximize and not self.config.headless:
            self._add_args(options, "--start-maximized")
            Logger.info("Start maximized")
        else:
            self._add_args(options, f"--window-size={self.config.window_width},{self.config.window_height}")
            Logger.info(f"Window size: {self.config.window_width}x{self.config.window_height}")

    # ================================
    #         HELPER HOOKS
    # ================================

    # helper hook (subclass can override)
    def _add_headless(self, options: Any) -> None:
        """Default: Chromium flag (Firefox subclass can override)."""
        try:
            options.add_argument("--headless=new")
        except Exception:
            # firefox uses different flag; subclass can override
            pass

    def _add_args(self, options: Any, *args: str) -> None:
        try:
            for a in args:
                options.add_argument(a)
        except Exception:
            pass

    def _set_chromium_prefs(self, options: Any, prefs: Dict) -> None:
        """Default Chrome-style prefs; subclass Firefox override if needed."""
        try:
            options.add_experimental_option("prefs", prefs)
        except Exception:
            pass

    def _set_capabilities(self, options: Any, caps: dict) -> None:
        for k, v in (caps or {}).items():
            options.set_capability(k, v)

    # ================================
    #         JSON OVERRIDES
    # ================================

    def _json_path(self) -> Path | None:
        p = os.getenv("BROWSER_CONFIG_PATH") or "config/configuration.json"
        pp = Path(p)
        return pp if pp.is_file() else None

    def _load_json_block(self) -> dict:
        """
        Get block JSON by provider name:
        {
          "chrome": {...},
          "edge": {...},
          "firefox": {...}
        }
        """
        Logger.info(f"Loading JSON configuration from: {self._json_path()}")
        p = self._json_path()
        if not p:
            return {}
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            block = data.get(self.name, {})
            return block if isinstance(block, dict) else {}
        except Exception:
            return {}

    def _apply_overrides_from_json(self, options: Any) -> None:
        """Apply standard options: args, prefs, capabilities"""
        Logger.debug("Applying overrides from JSON configuration...")
        b = self._load_json_block()
        if not b:
            return

        # headless from json just active if there is no HEADLESS on ENV
        if os.getenv("HEADLESS") is None and isinstance(b.get("headless"), bool) and b["headless"]:
            self._add_headless(options)

        for a in b.get("args", []) or []:
            self._add_args(options, str(a))

        # capabilities (W3C standard; vendor keys must have a colon :)
        caps = b.get("capabilities")
        if isinstance(caps, dict):
            self._set_capabilities(options, caps)

        # prefs: default Chromium format; Firefox will override processing in subclass
        prefs = b.get("prefs")
        if isinstance(prefs, dict):
            self._set_chromium_prefs(options, prefs)

        # Return vendor keys (ms:edgeOptions, moz:firefoxOptions, goog:chromeOptions) to subclass
        self._apply_vendor_json(options, b)

    def _apply_vendor_json(self, options: Any, block: dict) -> None:
        """Subclasses handle vendor keys from block (noop mặc định)."""
        return







