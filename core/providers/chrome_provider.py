from abc import ABC
from typing import Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from core.providers.browser_provider import BrowserProvider
from core.providers.registry import register_provider


@register_provider
class ChromeProvider(BrowserProvider, ABC):
    name = "chrome"
    aliases = ["google-chrome", "chromium", "gc"]

    def build_options(self):
        opts = ChromeOptions()
        return opts

    def _add_headless(self, options):
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    def apply_vendor_overrides(self, options):
        vendor = self.config.vendor_caps.get(self.name, {})
        gco = vendor.get("goog:chromeOptions")
        if gco:
            if "excludeSwitches" in gco:
                options.add_experimental_option("excludeSwitches", gco["excludeSwitches"])
            if "args" in gco:
                for a in gco["args"]:
                    options.add_argument(a)
            if "prefs" in gco:
                options.add_experimental_option("prefs", gco["prefs"])

    def create_local_driver(self, options: Any) -> WebDriver:
        return webdriver.Chrome(options)
