from __future__ import annotations

import datetime
import os
import time
from typing import Callable, Iterable, Optional, Type, TypeVar, Union

from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        WebDriverException)
from selenium.webdriver.remote.webdriver import WebDriver

from core.logging.logging import Logger
from core.report.reporting import AllureReporter

T = TypeVar("T")


class TimeoutErrorWithScreenShot(AssertionError):
    """Custom exception raised when a wait condition times out."""

    def __init__(self, message: str, screenshot_path: Optional[str] = None):
        super().__init__(message)
        self.screenshot_path = screenshot_path


class Waiter:
    """
    A utility class for waiting until a condition is met, similar to Selenium's WebDriverWait.
    It includes enhanced features like specific timeout messages and automatic screenshot on failure.
    """

    def __init__(self, timeout_s: float = 4.0,
                 poll_s: float = 0.2,
                 _clock: Callable[[], float] = time.monotonic):
        self.timeout_s = timeout_s
        self.poll_s = poll_s
        self._clock = _clock

    def until(self,
              supplier: Callable[[], T],
              on_timeout: Callable[[], str],
              ignored_exceptions: Optional[Iterable[Type[BaseException]]] = (
                      NoSuchElementException,
                      StaleElementReferenceException),
              ) -> T:

        end = self._clock() + max(0.0, self.timeout_s)
        last_exc: Optional[BaseException] = None
        polls = 0

        while True:
            try:
                polls += 1
                value = supplier()
                if value:  # Return if truthy
                    return value
            except BaseException as e:
                if ignored_exceptions and isinstance(e, tuple(ignored_exceptions)):
                    last_exc = e
                else:
                    raise

            if self._clock() >= end:
                break
            time.sleep(self.poll_s)

        driver = DriverManager.get_current_driver()
        if driver is not None:
            try:
                AllureReporter.attach_page_screenshot(driver, name="Timeout Screenshot")
            except Exception as e:
                Logger.info(f"Failed to attach screenshot via AllureReporter: {e}")

        detail = on_timeout()
        elapsed = max(0.0, self.timeout_s)

        msg = f"Timeout after {elapsed:.3f}s (polls={polls}): {detail}"

        if last_exc:
            msg += f"\nLast error: {type(last_exc).__name__}: {last_exc}"

        raise TimeoutErrorWithScreenShot(msg)

    def until_not(
            self,
            predicate: Callable[[], bool],
            on_timeout: Callable[[], str],
            ignored_exceptions: Optional[Iterable[Type[BaseException]]] = (NoSuchElementException,
                                                                           StaleElementReferenceException),
    ) -> bool:
        return self.until(lambda: not predicate(), on_timeout, ignored_exceptions)
