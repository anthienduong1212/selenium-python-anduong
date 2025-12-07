from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver

from core.driver.providers.browser_provider import BrowserProvider
from core.driver.providers.registry import register_provider
from core.logging.logging import Logger


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
        gco = block.get("goog:chromeOptions")

        if isinstance(gco, dict):
            Logger.info("Applying vendor-specific Chrome JSON overrides (goog:chromeOptions)...")
            excl = gco.get("excludeSwitches")
            if isinstance(excl, list) and excl:
                try:
                    options.add_experimental_option("excludeSwitches", excl)
                    Logger.debug(f"Excluding Chrome switches: {excl}")
                except Exception:
                    Logger.warning(f"Could not exclude switches: {e}")
                    pass



