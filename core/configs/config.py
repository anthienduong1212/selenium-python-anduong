from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
from importlib.resources import files
from pathlib import Path
from typing import Type, Dict, List, Optional, Any
import json, os


@dataclass
class Configuration:
    browser: str = os.getenv("BROWSER", "chrome").lower()
    headless: bool = os.getenv("HEADLESS", "false").lower() == "true"
    remote_url: Optional[str] = os.getenv("REMOTE_URL", None)

    wait_timeout_ms: int = int(os.getenv("WAIT_TIMEOUT_MS", "4000"))
    polling_interval_ms: int = int(os.getenv("POLLING_INTERVAL_MS", "200"))
    page_load_timeout_ms: Optional[int] = None
    implicit_wait_ms: Optional[int] = None

    window_width: int = int(os.getenv("WINDOW_WIDTH", "1920"))
    window_height: int = int(os.getenv("WINDOW_HEIGHT", "1080"))
    maximize: bool = os.getenv("START_MAXIMIZED", "true").lower() == "true"

    auto_scroll: bool = os.getenv("AUTO_SCROLL", "true").lower() == "true"
    scroll_block: str = os.getenv("SCROLL_BLOCK", "center")
    header_offset_px: int = int(os.getenv("HEADER_OFFSET_PX", 0))
    scroll_backend: str = os.getenv("SCROLL_BACKEND", "js")

    browser_config_map: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    extra_args: Dict[str, List[str]] = field(default_factory=dict)
    extra_prefs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    extra_caps: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    vendor_caps: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    per_browser_remote_url: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_pytest_options(cls, config) -> "Configuration":
        """
        Create Configuration based on pytest command line parameters.
        Supports reading options: --browser, --headless, --remote-url (or --remote_url),
        --wait-timeout-ms, --polling-interval-ms, --page-load-timeout-ms, --implicit-wait-ms,
        --maximize, --browser-config.
        """
        cfg = cls()

        browser = config.getoption("browser", default=None)
        if browser:
            cfg.browser = browser

        if config.getoption("headless", default=False):
            cfg.headless = True

        remote = config.getoption("remote_url", default=None)  # Dest of remote url
        if remote:
            cfg.remote_url = remote

        cfg_json = config.getoption("browser_config", default=None)
        if cfg_json:
            cfg.load_browser_json(cfg_json)

        return cfg

    def load_browser_json(self, path: str) -> None:
        """
        Read JSON override per-browser. Support:
            1) File Path on disk (relative/absolute)
            2) Fallback: resource in package core. Configs
        """
        p = Path(path)
        if p.exists():
            text = p.read_text(encoding="utf-8")
        else:
            try:
                text = (files("core.configs").joinpath(p.name)).read_text(encoding="utf-8")
            except Exception as e:
                raise FileNotFoundError(f"Browser Configuration not found: {path}") from e

        try:
            data = json.load(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}") from e

        self.browser_config_map = {}
        for name, conf in data.items():
            # Parse data to map
            if not isinstance(conf, dict):
                continue
            key = name.lower()
            self.browser_config_map[key] = conf

            args = conf.get("args")
            if isinstance(args, list):
                self.extra_args = args

            prefs = conf.get("prefs")
            if isinstance(prefs, dict):
                self.extra_prefs = prefs

            caps = conf.get("capabilities")
            if isinstance(caps, dict):
                self.extra_caps = caps

            vendor = {vk: conf[vk] for vk in conf if isinstance(vk, str) and ":" in vk}
            if vendor:
                self.vendor_caps[key] = vendor

            if conf.get("remote_url"):
                self.per_browser_remote_url[key] = str(conf["remote_url"])

            if conf.get("wait_timeout_ms") is not None:
                self.wait_timeout_ms = int(conf["wait_timeout_ms"])

            if conf.get("polling_interval_ms") is not None:
                self.polling_interval_ms = int(conf["polling_interval_ms"])

            if conf.get("page_load_timeout_ms") is not None:
                self.page_load_timeout_ms = int(conf["page_load_timeout_ms"])

            if conf.get("implicit_wait_ms") is not None:
                self.implicit_wait_ms = int(conf["implicit_wait_ms"])

            if conf.get("maximize") is not None:
                self.maximize = bool(conf["maximize"])

    def get_browser_cfg(self, browser_name: str) -> Dict[str, Any]:
        """Return block of configuration from json by browser name (lowered-case)."""
        return self.browser_config_map.get(browser_name.lower(), {})

    def clone(self, **overrides) -> "Configuration":
        """
        Make a copy of the current config, possibly overriding some properties.
        Useful when you need to temporarily change some values ​​without affecting the original config.
        """
        clone_cfg = deepcopy(self)
        for k, v in overrides.items():
            if hasattr(clone_cfg, k):
                setattr(clone_cfg, k, v)
        return clone_cfg

    def to_dict(self) -> Dict[str, Any]:
        """Export as dict (useful for logging or debug)."""
        return {
            "browser": self.browser,
            "headless": self.headless,
            "remote_url": self.remote_url,
            "wait_timeout_ms": self.wait_timeout_ms,
            "polling_interval_ms": self.polling_interval_ms,
            "page_load_timeout_ms": self.page_load_timeout_ms,
            "implicit_wait_ms": self.implicit_wait_ms,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "maximize": self.maximize,
            "extra_args": self.extra_args,
            "extra_prefs": self.extra_prefs,
            "extra_caps": self.extra_caps,
            "vendor_caps": self.vendor_caps,
            "per_browser_remote_url": self.per_browser_remote_url
        }
