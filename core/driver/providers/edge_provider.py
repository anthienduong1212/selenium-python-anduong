from typing import Any

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.remote.webdriver import WebDriver

from core.driver.providers.browser_provider import BrowserProvider
from core.driver.providers.registry import register_provider
from core.logging.logging import Logger


@register_provider
class EdgeProvider(BrowserProvider):
    name = "edge"
    aliases = ["msedge", "microsoft-edge"]

    def build_options(self):
        return EdgeOptions()

    def create_local_driver(self, options: Any) -> WebDriver:
        Logger.info("Instantiating local Edge WebDriver...")
        return webdriver.Edge(options=options)

    def _apply_vendor_json(self, options: EdgeOptions, block: dict) -> None:
        mso = block.get("ms:edgeOptions")
        if isinstance(mso, dict):
            Logger.info("Applying vendor-specific Edge JSON overrides (ms:edgeOptions)...")
            excl = mso.get("excludeSwitches")
            if isinstance(excl, list) and excl:
                try:
                    options.add_experimental_option("excludeSwitches", excl)
                    Logger.debug(f"Excluding Edge switches: {excl}")
                except Exception:
                    Logger.warning(f"Could not exclude switches: {e}")
                    pass


