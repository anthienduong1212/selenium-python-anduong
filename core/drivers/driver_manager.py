from __future__ import annotations

import threading
import atexit
import os
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, Any, Callable

from selenium.webdriver.remote.webdriver import WebDriver
from core.configs.config import Configuration
from core.drivers.driver_factory import DriverFactory

try:
    import allure
except Exception:
    allure = None


@dataclass
class _DriverRecord:
    driver: WebDriver
    config: Configuration


class DriverManager:
    """
    Managing WebDriver in test context:
        - Each thread/worker has its own instance (thread-safe, xdist-safe).
        - get_driver(cfg): create or reuse a live driver.
        - get_current_driver(): get the driver if it has been created in the context.
        - quit_driver(): close the current driver.
        - cleanup_all(): close all drivers that are still held (when atexit).
    """

    #  key = (process_id, worker_id, thread_id, context_id) -> _DriverRecord
    _REGISTRY: Dict[Tuple[int, str, int, int], _DriverRecord] = {}
    _LOCK = threading.RLock()

    # context var to distinguish async context if used (future safe)
    _CTX_ID: ContextVar[int] = ContextVar("_ctx_id", default=0)
    _NEXT_CTX_ID = 1

    _DEFAULT_BROWSER_JSON = os.getenv("BROWSER_CONFIG", "core/configs/config.json")
    _DEFAULT_PROVIDER_PACKGAGE = os.getenv("BROWSER_PROVIDER", "core.providers")

    # ______ public API _________
    @classmethod
    def get_driver(cls, cfg: Optional[Configuration] = None) -> WebDriver:
        """
        Create (or reuse) a driver for the current context.
        Prioritize live drivers; create a new one if dead.
        """
        cfg = cfg or Configuration()

        key = cls._current_key()
        with cls._LOCK:
            rec = cls._REGISTRY.get(key)
            if rec and cls._is_alive(rec.driver):
                return rec.driver

            if rec:
                cls._safe_quit(rec.driver)
                cls._REGISTRY.pop(key, None)

            driver = cls._create_driver(cfg)
            cls._post_create_setup(driver, cfg)

            cls._REGISTRY[key] = _DriverRecord(driver=driver, config=cfg)
            return driver

    @classmethod
    def get_current_driver(cls) -> Optional[WebDriver]:
        """Return current webdriver in registry of context (if created)"""
        key = cls._current_key()
        with cls._LOCK:
            rec = cls._REGISTRY.get(key)
            return rec.driver if rec else None

    @classmethod
    def quit_driver(cls) -> None:
        key = cls._current_key()
        with cls._LOCK:
            rec = cls._REGISTRY.pop(key, None)
        if rec:
            cls._safe_quit(rec.driver)

    @classmethod
    def cleanup_all(cls) -> None:
        with cls._LOCK:
            items = list(cls._REGISTRY.items())
            cls._REGISTRY.clear()
        for _, rec in items:
            cls._safe_quit(rec.driver)

    @classmethod
    def _create_driver(cls, cfg: Configuration) -> WebDriver:
        """
        Create driver via DriverFactory (discovered providers).
        Support JSON file to configure default browsers.
        :param cfg:
        :return WebDriver:
        """
        factory = DriverFactory(provider_package=cls._DEFAULT_PROVIDER_PACKGAGE)
        driver = factory.create_driver(cfg)
        return driver

    @classmethod
    def _current_key(cls) -> Tuple[int, str, int, int]:
        """
        Generate distinguishing key by:
        - Process PID (each xdist worker is a process)
        - worker id (PYTEST_XDIST_WORKER), fallback 'main'
        - thread id (each xdist test runs in its own thread)
        - context id (if using contextvars)
        """
        pid = os.getpid()
        worker = os.getenv("PYTEST_XDIST_WORKER", "main")
        tid = threading.get_ident()
        ctx = cls._CTX_ID.get()
        return pid, worker, tid, ctx

    @classmethod
    def new_context(cls) -> int:
        """Create new context id; using when need to have more than 1 driver in a thread."""
        new_id = getattr(cls._CTX_ID, "next", 1)
        cls._CTX_ID.value = new_id
        cls._CTX_ID.next = new_id + 1
        return new_id

    @classmethod
    def reset_context(cls) -> None:
        """Reset context to 0."""
        cls._CTX_ID.value = 0

    @classmethod
    def _is_alive(cls, driver: WebDriver) -> bool:
        """
        Check if the driver is alive.
        The easy way: call a small command with try/except.
        """
        try:
            _ = driver.current_url
            return True
        except Exception:
            return False

    @classmethod
    def _safe_quit(cls, driver: WebDriver) -> None:
        """Safe quit + attach Allure if possible"""
        try:
            if allure:
                try:
                    png = driver.get_screenshot_as_png()
                    allure.attach(png, name="Final Screenshot", attachment_type=allure.attachment_type.PNG)
                except Exception:
                    pass
            driver.quit()
        except Exception:
            # swallow quit error so as not to ruin teardown
            pass

    @classmethod
    def _post_create_setup(cls, driver: WebDriver, cfg: Configuration) -> None:
        """Setup after create WebDriver: timeout, windows size, implicit wait"""
        implicit_ms = getattr(cfg, "implicit_wait_ms", 0)
        if implicit_ms and hasattr(driver, "implicit_wait"):
            driver.implicit_wait(max(0.0, implicit_ms / 1000.0))

        try:
            if getattr(cfg, "maximize", False):
                driver.maximize_window()
            else:
                w = getattr(cfg, "window_width", None)
                h = getattr(cfg, "window_height", None)
                if w and h:
                    driver.set_window_size(int(w), int(h))
        except Exception:
            pass

        try:
            pl_ms = getattr(cfg, "page_load_timeout_ms", None)
            if pl_ms and hasattr(driver, "set_page_load_timeout"):
                driver.set_page_load_timeout(max(0.0, pl_ms / 1000.0))
        except Exception:
            pass


# Register cleanup when program end
atexit.register(DriverManager.cleanup_all)
