# core/providers/edge_provider.py
from abc import ABC

from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from core.providers.base_provider import BrowserProvider
from core.providers.registry import register_provider


@register_provider
class EdgeProvider(BrowserProvider, ABC):
    name = "edge"
    aliases = ["msedge", "microsoft-edge"]

    def build_options(self):
        return EdgeOptions()

    def build_service(self):
        return EdgeService(EdgeChromiumDriverManager().install())

    def apply_vendor_overrides(self, options):
        vendor = self.config.vendor_caps.get(self.name, {})
        mso = vendor.get("ms:edgeOptions")
        if mso:
            if "excludeSwitches" in mso:
                options.add_experimental_option("excludeSwitches", mso["excludeSwitches"])
            if "args" in mso:
                for a in mso["args"]:
                    options.add_argument(a)

    def create_local_driver(self, options, service):
        return webdriver.Edge(service=service, options=options)
