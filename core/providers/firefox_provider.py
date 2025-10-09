from abc import ABC
from typing import Any, Optional, Dict

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager
from core.providers.base_provider import BrowserProvider
from core.providers.registry import register_provider


@register_provider
class FirefoxProvider(BrowserProvider, ABC):
    name = "firefox"
    aliases = ["mozilla-firefox", "ff", "firefox"]

    def build_options(self) -> Any:
        opts = FirefoxOptions()
        return opts

    def build_service(self) -> Optional[Any]:
        return FirefoxService(GeckoDriverManager().install())

    def _add_headless(self, options: Any):
        options.add_argument("--headless")

    def _set_prefs(self, options: Any, prefs: Dict):
        for k, v in prefs.items():
            try:
                options.set_preference(k, v)
            except Exception:
                pass

    def apply_vendor_overrides(self, options):
        vendor = self.config.vendor_caps.get(self.name, {})
        mfo = vendor.get("moz:firefoxOptions")
        if not mfo:
            return
        # args
        if "args" in mfo:
            for a in mfo["args"]:
                options.add_argument(a)
        # log.level
        try:
            log_block = mfo.get("log", {})
            if "level" in log_block and hasattr(options, "log"):
                # Selenium Python hỗ trợ options.log.level
                options.log.level = log_block["level"]
        except Exception:
            pass

    def create_local_driver(self, options, service):
        return webdriver.Firefox(service=service, options=options)
