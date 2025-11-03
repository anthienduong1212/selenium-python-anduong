from __future__ import annotations
import json, os
from dataclasses import dataclass, field
from copy import deepcopy
from importlib.resources import files
from pathlib import Path
from typing import Type, Dict, List, Optional, Any
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
    try:
        return None if raw is None else int(raw)
    except (TypeError, ValueError):
        return default


def _coerce_bool(v) -> Optional[bool]:
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in _TRUE:
        return True
    if s in _FALSE:
        return False
    return None


def _coerce_int(v) -> Optional[int]:
    try:
        return None if v is None else int(v)
    except (TypeError, ValueError):
        return None


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
    scroll_backend: str = os.getenv("SCROLL_BACKEND", "js")  # js | wheel | move

    # ================================
    #          FACTORIES
    # ================================

    @classmethod
    def from_cli_file(cls, cli_path: Optional[str] = None) -> "Configuration":
        """
        ENV is default. If configuration is available:
            - Prioritize CLI --browser-config
            - If not, default path: config/configuration.json
        """
        cfg = cls()

        path = Path(cli_path) if cli_path else Path("resources/config.json")
        if path.is_file():
            cfg.apply_overrides_from_file(path)
        return cfg

    def apply_overrides_from_file(self, path: Path) -> None:
        data = json.loads(path.read_text("utf-8"))
        Logger.info(f"Loaded configuration from {path}")
        if not isinstance(data, dict):
            return

        # Only permit these field
        cast_map: Dict[str, Any] = {
            "browser": lambda v: str(v).lower(),
            "headless": _coerce_bool,
            "remote_url": lambda v: str(v),

            "wait_timeout_ms": _coerce_int,
            "polling_interval_ms": _coerce_int,
            "page_load_timeout_ms": _coerce_int,
            "implicit_wait_ms": _coerce_int,

            "window_width": _coerce_int,
            "window_height": _coerce_int,
            "maximize": _coerce_bool,

            "auto_scroll": _coerce_bool,
            "scroll_block": lambda v: str(v),
            "header_offset_px": _coerce_int,
            "scroll_backend": lambda v: str(v),
        }

        for k, caster in cast_map.items():
            if k in data and data[k] is not None:
                val = caster(data[k])
                if val is not None:
                    setattr(self, k, val)

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
