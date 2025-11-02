from abc import ABC
from typing import Any
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from core.driver.providers.browser_provider import BrowserProvider
from core.driver.providers.registry import register_provider


def _env_csv(key: str) -> list[str]:
    v = os.getenv(key, "")
    return [x.strip() for x in v.split(",") if x.strip()]


def _env_json_obj(key: str) -> dict | None:
    raw = os.getenv(key)
    if not raw: return None
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else None
    except Exception:
        return None

@register_provider
class ChromeProvider(BrowserProvider, ABC):
    name = "chrome"
    aliases = ["google-chrome", "chromium", "gc"]

    def build_options(self):
        opts = ChromeOptions()
        return opts

    def create_local_driver(self, options: Any) -> WebDriver:
        return webdriver.Chrome(options)

    def apply_vendor_overrides(self, options):

        for a in _env_csv("CHROME_ARGS"):
            self._add_args(options, a)

        prefs = _env_json_obj("CHROME_PREFS_JSON")
        if prefs:
            self._set_chromium_prefs(options, prefs)

        excl = _env_csv("CHROME_EXCLUDE_SWITCHES")
        if excl:
            try:
                options.add_experimental_option("excludeSwitches", excl)
            except Exception:
                pass

    def _apply_vendor_json(self, options: ChromeOptions, block: dict) -> None:
        gco = block.get("goog:chromeOptions")
        if isinstance(gco, dict):
            # theo Selenium/Chromium: args, prefs, excludeSwitches...
            for a in gco.get("args", []) or []:
                self._add_args(options, str(a))
            prefs = gco.get("prefs")
            if isinstance(prefs, dict):
                self._set_chromium_prefs(options, prefs)
            excl = gco.get("excludeSwitches")
            if isinstance(excl, list) and excl:
                try:
                    options.add_experimental_option("excludeSwitches", excl)
                except Exception:
                    pass



