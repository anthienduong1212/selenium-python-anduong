from abc import ABC
from typing import Any, Optional, Dict
import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.firefox import GeckoDriverManager
from core.providers.browser_provider import BrowserProvider
from core.providers.registry import register_provider


def _env_json_obj(key: str) -> dict | None:
    raw = os.getenv(key)
    if not raw: return None
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else None
    except Exception:
        return None


@register_provider
class FirefoxProvider(BrowserProvider, ABC):
    name = "firefox"
    aliases = ["mozilla-firefox", "ff", "firefox"]

    def build_options(self) -> Any:
        opts = FirefoxOptions()
        return opts

    def _add_headless(self, options: FirefoxOptions):
        options.add_argument("--headless")

    def _set_prefs(self, options: Any, prefs: Dict):
        for k, v in prefs.items():
            try:
                options.set_preference(k, v)
            except Exception:
                pass

    def apply_vendor_overrides(self, options):
        prefs = _env_json_obj("FIREFOX_PREFS_JSON")
        if prefs:
            for k, v in prefs.items():
                try:
                    options.set_preference(k, v)  # Firefox dùng set_preference cho prefs.
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

        mfo = block.get("moz:firefoxOptions")
        if isinstance(mfo, dict):
            # cách đơn giản & đúng chuẩn: set capability vendor-prefixed.
            options.set_capability("moz:firefoxOptions", mfo)

    def create_local_driver(self, options: Any) -> WebDriver:
        return webdriver.Firefox(options)
