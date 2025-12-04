from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import dataclass, field
from dataclasses import replace as dc_replace
from importlib import resources
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from core.logging.logging import Logger

# ================================
#          HELPER
# ================================

_TRUE = {"1", "true", "t", "yes", "y", "on"}
_FALSE = {"0", "false", "f", "no", "n", "off"}


def env_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default

    v = raw.strip().lower()
    if v in _TRUE:
        return True
    if v in _FALSE:
        return False
    raise ValueError(f"Invalid boolean for {key}={raw!r}. "
                     f"Use one of {_TRUE | _FALSE}.")


def env_int(key: str, default: int | None) -> Optional[int]:
    raw = os.getenv(key, None if default is None else str(default))
    return None if raw is None else int(raw)


# ================================
#          CONFIGURATION
# ================================


@dataclass
class Configuration:
    browser: str = os.getenv("BROWSER", "chrome").lower()
    headless: bool = env_bool("HEADLESS", False)
    remote_url: Optional[str] = os.getenv("REMOTE_URL")

    wait_timeout_ms: int = env_int("WAIT_TIMEOUT_MS", 4000) or 4000
    polling_interval_ms: int = env_int("POLLING_INTERVAL_MS", 200) or 200
    page_load_timeout_ms: Optional[int] = env_int("PAGE_LOAD_TIMEOUT_MS", None)
    implicit_wait_ms: Optional[int] = env_int("IMPLICIT_WAIT_MS", None)

    window_width: int = env_int("WINDOW_WIDTH", 1920) or 1920
    window_height: int = env_int("WINDOW_HEIGHT", 1080) or 1080
    maximize: bool = env_bool("START_MAXIMIZED", True)

    auto_scroll: bool = env_bool("AUTO_SCROLL", True)
    scroll_block: str = os.getenv("SCROLL_BLOCK", "center")
    header_offset_px: int = env_int("HEADER_OFFSET_PX", 0) or 0
    scroll_backend: str = os.getenv("SCROLL_BACKEND", "wheel")  # js | wheel | move

    per_browser_remote_url: Optional[Dict[str, str]] = field(default_factory=dict)
    _json_data: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    # ================================
    #          FACTORIES
    # ================================

    @classmethod
    def config_source_detection(cls, cli_path: Optional[str] = None) -> Optional[Path]:
        """
        Precedence:
        1) CLI --browser-config
        2) ENV BROWSER_CONFIG_PATH
        3) Package resource: yourpkg/resources/configuration.json
        """

        if cli_path:
            p = Path(cli_path).expanduser()
            Logger.info(f"Loading config from {cli_path}")
            if p.exists():
                return p

        path_from_env = os.getenv("BROWSER_CONFIG_PATH")
        if path_from_env:
            p = Path(path_from_env).expanduser()
            Logger.info(f"Loading config from env {path_from_env}")
            if p.exists():
                return p

        try:
            base = resources.files("resources")
            p = base / "configuration.json"
            if p.is_file():
                Logger.info(f"Loading default config from resources")
                return p
        except Exception:
            Logger.debug("No default configuration file")
            pass

    @classmethod
    def from_sources(cls, *, cli_browser_config_path: Optional[str] = None, **overrides) -> "Configuration":
        """
        Create Configuration and load JSON once (cache into _json_data) in order:
        CLI > ENV > package resource. Then merge JSON > defaults/ENV (if you have one).
        """
        cfg = cls()

        p = cls.config_source_detection(cli_browser_config_path)
        json_data: Dict[str, Any] = {}

        if p is not None:
            try:
                Logger.debug("Reading config from json")
                raw = p.read_text(encoding="utf-8")
                json_data = json.loads(raw) or {}
            except Exception:
                json_data = {}
                Logger.error("There is no configuration load")

        updates = {}
        for key in cfg.to_dict().keys():
            if key in json_data:
                updates[key] = json_data[key]

        updates['_json_data'] = deepcopy(json_data)

        cfg = dc_replace(cfg, **updates)

        # Create new cfg with value from parameter of from_sources, if there aren't new overrides params, do nothing
        cfg = cfg.replace(**overrides)

        cfg = cfg.replace(browser=cfg.browser.strip().lower())
        return cfg

    def replace(self, **overrides) -> "Configuration":

        merge_keys = ("extra_caps", "per_browser_remote_url")
        merged: Dict[str, Any] = {}

        for k in merge_keys:
            if k in overrides and overrides[k] is not None:
                current_val = getattr(self, k) or {}
                incoming = overrides.pop(k) or {}
                merged[k] = {**current_val, **incoming}

        if "browser" in overrides and overrides["browser"]:
            merged["browser"] = str(overrides.pop("browser")).strip().lower()

        # Return a new configuration instance with new _json_data
        return dc_replace(self, **overrides, **merged)

    def json_global(self) -> Dict[str, Any]:
        return self._json_data if isinstance(self._json_data, dict) else {}

    def json_browser_block(self, name: Optional[str] = None) -> Dict[str, Any]:
        key = (name or self.browser or "").strip().lower()
        data = self.json_global()
        block = data.get(key, {}) if isinstance(data, dict) else {}
        return block if isinstance(block, dict) else {}

    # ================================
    #          DEBUG / LOGGING
    # ================================

    def to_dict(self) -> Dict[str, Any]:
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
            "auto_scroll": self.auto_scroll,
            "scroll_block": self.scroll_block,
            "header_offset_px": self.header_offset_px,
            "scroll_backend": self.scroll_backend,
        }
