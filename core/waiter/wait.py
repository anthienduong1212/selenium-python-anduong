from __future__ import annotations

import datetime
import os
import time
from typing import Callable, Sequence, Optional, Type, TypeVar, Union

from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        WebDriverException)
from selenium.webdriver.remote.webdriver import WebDriver

from core.driver.driver_manager import DriverManager
from core.logging.logging import Logger
from core.report.reporting import AllureReporter

T = TypeVar("T")


class TimeoutErrorWithScreenShot(AssertionError):
    """Custom exception raised when a wait condition times out."""

    def __init__(self, message: str):
        super().__init__(message)


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
              ignored_exceptions: Sequence[Type[BaseException]] = (
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
                if value:
                    return value
            except BaseException as e:
                if isinstance(e, tuple(ignored_exceptions)):
                    last_exc = e
                else:
                    raise

            if self._clock() >= end:
                break
            time.sleep(self.poll_s)

        detail = on_timeout()
        elapsed = max(0.0, self.timeout_s)
        msg = f"Timeout after {elapsed:.3f}s (polls={polls}): \n{on_timeout()}"

        if last_exc:
            Logger.error(f"Waiting failed due to last exception. Details: {detail}")
            raise last_exc

        AllureReporter.attach_page_screenshot(name="Timeout Screenshot")
        AllureReporter.attach_text(msg, str(BaseException))

    def until_not(
            self,
            predicate: Callable[[], bool],
            on_timeout: Callable[[], str],
            ignored_exceptions: Optional[Sequence[Type[BaseException]]] = (NoSuchElementException,
                                                                           StaleElementReferenceException),
    ) -> bool:
        return self.until(lambda: not predicate(), on_timeout, ignored_exceptions)
