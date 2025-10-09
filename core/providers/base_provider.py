from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from selenium.webdriver.remote.webdriver import WebDriver
from core.configs.config import Configuration


class BrowserProvider(ABC):
    """
   Abstract provider: subclass implements option/service creation.
   Base class handles create_driver() logic (local vs remote) to avoid duplication.
   """

    name: str = None
    aliases: List[str] = []

    def __init__(self, config: Configuration):
        self.config = config
        self.browser_cfg = config.get_browser_cfg(self.name)

    @abstractmethod
    def build_options(self) -> Any:
        """Return browser-specific Options instance (ChromeOptions/FirefoxOptions/EdgeOptions)."""
        raise NotImplementedError

    @abstractmethod
    def build_service(self) -> Optional[Any]:
        """Return Service instance or None (if using Selenium Manager or remote)."""
        raise NotImplementedError

    def apply_common_settings(self, options: Any):
        if self.config.headless:
            # keep browser-specific headless flag in subclass or here by convention
            self._add_headless(options)

        if self.config.maximize:
            self._add_args(options, "--start-maximized")
        else:
            self._add_args(options, f"--window-size={self.config.window_width},{self.config.window_height}")

        # extra args from config by provider name
        for arg in self.config.extra_args.get(self.name, []):
            self._add_args(options, arg)

        # add prefs if provider supplies API for that
        prefs = self.config.extra_prefs.get(self.name)
        if prefs:
            self._set_prefs(options, prefs)

        # add extra capabilities dict
        caps = self.config.extra_caps.get(self.name)
        if caps:
            for k, v in caps.items():
                options.set_capability(k, v)

    # helper hook (subclass can override)
    def _add_headless(self, options: Any):
        try:
            options.add_argument("--headless=new")
        except Exception:
            # firefox uses different flag; subclass can override
            pass

    def _add_args(self, options: Any, arg: str):
        try:
            options.add_argument(arg)
        except Exception:
            pass

    def _set_prefs(self, options: Any, prefs: Dict):
        # default for Chrome-style
        try:
            options.add_experimental_option("prefs", prefs)
        except Exception:
            # subclass can support set_preference for Firefox
            pass

    def create_driver(self) -> WebDriver:
        options = self.build_options()
        self.apply_common_settings(options)

        self.apply_vendor_overrides(options)

        self.apply_vendor_capabilities(options)

        remote_url = self.config.per_browser_remote_url.get(self.name) or self.config.remote_url
        if remote_url:
            return self.create_remote_driver(options, remote_url)

        service = self.build_service()
        return self.create_local_driver(options, service)

    def apply_vendor_overrides(self, options: Any):
        pass

    def apply_vendor_capabilities(self, options: Any):
        vendor = self.config.vendor_caps.get(self.name, {})
        for k, v in vendor.items():
            options.set_capability(k, v)

    @abstractmethod
    def create_local_driver(self, options: Any, service: Optional[Any]) -> WebDriver:
        """Instantiate a local WebDriver using options and service."""
        raise NotImplementedError

    def create_remote_driver(self, options: Any, remote_url: str) -> WebDriver:
        """Default remote creation uses webdriver.Remote(options=options)."""
        from selenium import webdriver
        return webdriver.Remote(command_executor=remote_url, options=options)

