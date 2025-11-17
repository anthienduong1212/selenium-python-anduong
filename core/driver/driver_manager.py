from __future__ import annotations

import atexit
import os
import sys
import threading
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple, Type

from selenium.common.exceptions import (InvalidArgumentException,
                                        NoSuchWindowException,
                                        TimeoutException, WebDriverException)
from selenium.webdriver.remote.webdriver import WebDriver

from core.configuration.configuration import Configuration
from core.constants.constants import Constants
from core.driver.driver_factory import DriverFactory
from core.logging.logging import Logger
from core.report.reporting import AllureReporter


@dataclass
class _DriverRecord:
    """Dataclass to hold the WebDriver instance and its configuration."""
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

    #  key = (process_id, thread_id, context_id) -> _DriverRecord
    _REGISTRY: Dict[Tuple[int, int, int], _DriverRecord] = {}
    _LOCK = threading.RLock()

    _ctx_id: ContextVar[int] = ContextVar("_ctx_id", default=0)
    _next_ctx_id: int = 1

    _DEFAULT_PROVIDER_PACKAGE = Constants.BROWSER_PROVIDER

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
    def get_current_config(cls) -> Optional[Configuration]:
        """Return current configuration in registry of context"""
        key = cls._current_key()
        with cls._LOCK:
            rec = cls._REGISTRY.get(key)
            return rec.config if rec else None

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
        :param cfg: Configuration
        :return WebDriver: WebDriver created from factory
        """
        factory = DriverFactory(provider_package=cls._DEFAULT_PROVIDER_PACKAGE)
        driver = factory.create_driver(cfg)
        return driver

    @classmethod
    def _current_key(cls) -> Tuple[int, int, int]:
        """
        Generate distinguishing key by:
        - Process PID (each xdist worker is a process)
        - thread id (each xdist test runs in its own thread)
        - context id (if using contextvars)
        """
        pid = os.getpid()
        tid = threading.get_ident()
        ctx = cls._ctx_id.get()
        return pid, tid, ctx

    @classmethod
    def new_context(cls) -> int:
        """Create new context id; using when need to have more than 1 driver in a thread."""
        with cls._LOCK:
            new_id = cls._next_ctx_id
            cls._next_ctx_id += 1
            cls._ctx_id.set(new_id)
        return new_id

    @classmethod
    def reset_context(cls) -> None:
        """Reset context to 0"""
        cls._ctx_id.set(0)

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
            AllureReporter.attach_page_screenshot(driver, name="Final Screenshot")
        except Exception as e:
            Logger.error(f"Error when capturing Allure screenshot: {e}")
        try:
            driver.quit()
        except Exception as e:
            Logger.debug(f"Error when closing driver: {e}")

    @classmethod
    def _post_create_setup(cls, driver: WebDriver, cfg: Configuration) -> None:
        """Setup after create WebDriver: timeout, windows size, implicit wait"""
        implicit_ms = int(getattr(cfg, "implicit_wait_ms", 0) or 0)
        if implicit_ms > 0:
            driver.implicit_wait(implicit_ms / 1000.0)

        try:
            if getattr(cfg, "maximize", False):
                driver.maximize_window()
            else:
                w = getattr(cfg, "window_width", None)
                h = getattr(cfg, "window_height", None)
                if w and h:
                    driver.set_window_size(int(w), int(h))
        except (NoSuchWindowException, WebDriverException) as e:
            Logger.error(f"Error when settings windows size: {e}")

        try:
            pl_ms = getattr(cfg, "page_load_timeout_ms", None)
            if pl_ms and hasattr(driver, "set_page_load_timeout"):
                driver.set_page_load_timeout(max(0.0, pl_ms / 1000.0))
        except TimeoutException as e:
            Logger.error(f"Error when settings page load timeout: {e}")


# Register cleanup when program end
atexit.register(DriverManager.cleanup_all)
