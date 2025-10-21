from abc import ABC
from typing import Any, Optional

from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from core.providers.browser_provider import BrowserProvider
from core.providers.registry import register_provider


@register_provider
class EdgeProvider(BrowserProvider, ABC):
    name = "edge"
    aliases = ["msedge", "microsoft-edge"]

    def build_options(self):
        return EdgeOptions()

    def apply_vendor_overrides(self, options):
        vendor = self.config.vendor_caps.get(self.name, {})
        mso = vendor.get("ms:edgeOptions")
        if mso:
            if "excludeSwitches" in mso:
                options.add_experimental_option("excludeSwitches", mso["excludeSwitches"])
            if "args" in mso:
                for a in mso["args"]:
                    options.add_argument(a)

    def create_local_driver(self, options: Any) -> WebDriver:
        return webdriver.Edge(options)
