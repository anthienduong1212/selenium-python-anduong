import json
import os
from typing import Any, Dict

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver

from core.driver.providers.browser_provider import BrowserProvider
from core.logging.logging import Logger
from core.driver.providers.registry import register_provider


@register_provider
class FirefoxProvider(BrowserProvider):
    name = "firefox"
    aliases = ["mozilla-firefox", "ff", "firefox"]

    def build_options(self) -> Any:
        opts = FirefoxOptions()
        return opts

    def create_local_driver(self, options: Any) -> WebDriver:
        Logger.info("Instantiating local Firefox WebDriver...")
        return webdriver.Firefox(options=options)

    def _add_headless(self, options: FirefoxOptions):
        options.add_argument("--headless")

    def _set_prefs(self, options: Any, prefs: Dict):
        for k, v in prefs.items():
            try:
                options.set_preference(k, v)
            except Exception:
                pass

    def _apply_vendor_json(self, options: FirefoxOptions, block: dict) -> None:
        prefs = block.get("prefs")
        if isinstance(prefs, dict):
            for k, v in prefs.items():
                try:
                    options.set_preference(k, v)
                except Exception:
                    pass

        mfo = block.get("moz:firefoxOptions") or {}
        for a in (mfo.get("args") or []):
            options.add_argument(str(a))
        binary = mfo.get("binary")
        if isinstance(binary, dict) and binary.strip():
            options.binary_location = binary


