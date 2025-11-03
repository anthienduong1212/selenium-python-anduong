from abc import ABC
from typing import Any
import os
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
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
class EdgeProvider(BrowserProvider, ABC):
    name = "edge"
    aliases = ["msedge", "microsoft-edge"]

    def build_options(self):
        return EdgeOptions()

    def apply_vendor_overrides(self, options):
        return options

    def _apply_vendor_json(self, options: EdgeOptions, block: dict) -> None:
        # Edge is Chromium-based; has "ms:edgeOptions" (vendor prefixed).
        mso = block.get("ms:edgeOptions")
        if isinstance(mso, dict):
            for a in mso.get("args", []) or []:
                self._add_args(options, str(a))

            prefs = mso.get("prefs")
            if isinstance(prefs, dict):
                try:
                    options.add_experimental_option("prefs", prefs)
                except Exception:
                    pass

            excl = mso.get("excludeSwitches")
            if isinstance(excl, list) and excl:
                try:
                    options.add_experimental_option("excludeSwitches", excl)
                except Exception:
                    pass

    def create_local_driver(self, options: Any) -> WebDriver:
        return webdriver.Edge(options)
