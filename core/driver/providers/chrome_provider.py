import json
import os
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver

from core.driver.providers.browser_provider import BrowserProvider
from core.driver.providers.registry import register_provider
from core.logging.logging import Logger


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
class ChromeProvider(BrowserProvider):
    name = "chrome"
    aliases = ["google-chrome", "chromium", "gc"]

    def build_options(self):
        Logger.debug("Building Chrome options...")
        opts = ChromeOptions()
        return opts

    def create_local_driver(self, options: Any) -> WebDriver:
        Logger.info("Instantiating local Chrome WebDriver...")
        return webdriver.Chrome(options=options)

    def _apply_vendor_json(self, options: ChromeOptions, block: dict) -> None:
        Logger.info("Applying vendor-specific Chrome JSON overrides (goog:chromeOptions)...")
        gco = block.get("goog:chromeOptions")

        if isinstance(gco, dict):
            # theo Selenium/Chromium: args, prefs, excludeSwitches...
            for a in gco.get("args", []) or []:
                self._add_args(options, str(a))
                Logger.debug(f"Adding Chrome argument: {a}")

            prefs = gco.get("prefs")
            if isinstance(prefs, dict):
                self._set_chromium_prefs(options, prefs)
                Logger.debug("Setting Chrome preferences.")

            excl = gco.get("excludeSwitches")
            if isinstance(excl, list) and excl:
                try:
                    options.add_experimental_option("excludeSwitches", excl)
                    Logger.debug(f"Excluding Chrome switches: {excl}")
                except Exception:
                    Logger.warning(f"Could not exclude switches: {e}")
                    pass



