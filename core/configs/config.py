from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
import json, os
from typing import Type, Dict, List, Optional, Any


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
    def from_pytest_options(cls: Type["Configuration"], config) -> "Configuration":
        """
        Create Configuration based on pytest command line parameters.
        Supports reading options: --browser, --headless, --remote-url (or --remote_url),
        --wait-timeout-ms, --polling-interval-ms, --page-load-timeout-ms, --implicit-wait-ms,
        --maximize, --browser-config.
        """
        cfg = cls()

        def _to_int(v) -> Optional[int]:
            try:
                return int(v)
            except (TypeError, ValueError):
                return None

        def _to_bool(v) -> Optional[bool]:
            if isinstance(v, bool):
                return v
            if v is None:
                return None
            s = str(v).strip().lower()
            if s in {"1", "true", "yes", "y", "on"}:
                return True
            if s in {"0", "false", "no", "n", "off"}:
                return False
            return None

        b = config.getoption("--browser", default=None)
        if b:
            cfg.browser = str(b).lower()

        # headless (True/False)
        h = config.getoption("--headless", default=None)
        hb = _to_bool(h)
        if hb is not None:
            cfg.headless = hb

        # remote URL
        remote = config.getoption("--remote-url", default=None) or config.getoption("--remote_url", default=None)
        if remote:
            cfg.remote_url = str(remote)

        wto = _to_int(config.getoption("--wait-timeout-ms", default=None))
        if wto is not None:
            cfg.wait_timeout_ms = wto

        pti = _to_int(config.getoption("--polling-interval-ms", default=None))
        if pti is not None:
            cfg.polling_interval_ms = pti

        plo = _to_int(config.getoption("--page-load-timeout-ms", default=None))
        if plo is not None:
            cfg.page_load_timeout_ms = plo

        iwt = _to_int(config.getoption("--implicit-wait-ms", default=None))
        if iwt is not None:
            cfg.implicit_wait_ms = iwt

        m = config.getoption("--maximize", default=None)
        mb = _to_bool(m)
        if mb is not None:
            cfg.maximize = mb

        # Nạp file JSON override nếu có
        json_path = config.getoption("--browser-config", default=None)
        if json_path:
            cfg.load_browser_json(json_path)
            try:
                keys = list(cfg.browser_config_map.keys())
                if not cfg.browser and len(keys) == 1:
                    cfg.browser = keys[0].lower()
            except Exception:
                pass

        return cfg

    def load_browser_json(self, path: str) -> None:
        """
        Reads a JSON file containing browser-specific configuration and loads it into the current config.
        Supports overriding args, prefs, capabilities, vendor options and remote_url per‑browser.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Browser Configuration not found: {path}")

        self.browser_config_map = {}
        for name, conf in data.items():
            if not isinstance(conf, dict):
                continue
            key = name.lower()
            self.browser_config_map[key] = conf

            if isinstance(conf.get("args"), list):
                self.extra_args[key] = conf["args"]

            if isinstance(conf.get("prefs"), dict):
                self.extra_prefs[key] = conf["prefs"]

            if isinstance(conf.get("capabilities"), dict):
                self.extra_caps[key] = conf["capabilities"]

            # vendor-specific capabilities: accept every key with semicolon
            vendor = {vk: conf[vk] for vk in conf if isinstance(vk, str) and ":" in vk}
            if vendor:
                self.vendor_caps[key] = vendor

            # Override configuration by selected Browser
            b = (self.browser or "").lower()

            if not b and len(self.browser_config_map == 1):
                b = next(iter(self.browser_config_map))
                self.browser = b

            sel = self.browser_config_map.get(b, {})
            mapping = {
                "wait_timeout_ms": int,
                "polling_interval_ms": int,
                "page_load_timeout_ms": int,
                "implicit_wait_ms": int,
                "maximize": bool,
                "headless": bool,
                "remote_url": str,
            }

            for k, caster in mapping.items():
                if hasattr(self, k) and k in sel and sel[k] is not None:
                    setattr(self, k, caster(sel[k]))

    def get_browser_cfg(self, browser_name: str) -> Dict[str, Any]:
        """Trả về block cấu hình theo tên browser (đã lower-case)."""
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
