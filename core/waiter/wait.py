from __future__ import annotations
import time, os, datetime
from typing import Callable, Optional, Iterable, Type, TypeVar, Union
from selenium.common.exceptions import (
    WebDriverException,
    NoSuchElementException,
    StaleElementReferenceException,
)

T = TypeVar("T")


class TimeoutErrorWithScreenShot(AssertionError):
    def __init__(self, message: str, screenshot_path: Optional[str] = None):
        super().__init__(message)
        self.screenshot_path = screenshot_path


class Waiter:
    def __init__(self, timeout_s: float = 4.0,
                 poll_s: float = 0.2,
                 screen_dir: str = "reports/screenshots",
                 _clock: Callable[[], float] = time.monotonic):
        self.timeout_s = timeout_s
        self.poll_s = poll_s
        self.screen_dir = screen_dir

    def until(self,
              supplier: Callable[[], T],
              on_timeout: Callable[[], str],
              take_screenshot: Optional[Callable[[str], bool]] = None,
              ignored_exceptions: Optional[Iterable[Type[BaseException]]] = (
                      NoSuchElementException,
                      StaleElementReferenceException),
              ) -> T:

        end = time.time() + max(0.0, self.timeout_s)
        last_exc: Optional[BaseException] = None
        polls = 0

        while True:
            try:
                polls += 1
                value = supplier()
                if value:  # Return if truthy
                    return value
            except BaseException as e:
                # Just ignore temporary exception
                if ignored_exceptions and isinstance(e, tuple(ignored_exceptions)):
                    last_exc = e
                else:
                    raise

            # Check timeout after each poll
            if time.time() >= end:
                break
            time.sleep(self.poll_s)

        # Try to take screenshot (Handle availability)
        screenshot_path = None
        if take_screenshot:
            os.makedirs(self.screen_dir, exist_ok=True)
            name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".png"
            path = os.path.join(self.screen_dir, name)

            try:
                ok = take_screenshot(path)
                if ok:
                    screenshot_path = path
            except WebDriverException:
                pass

        # On timeout handle
        detail = on_timeout()
        elapsed = max(0.0, self.timeout_s)

        msg = f"Timeout after {elapsed:.3f}s (polls={polls}): {detail}"

        if last_exc:
            msg += f"\nLast error: {type(last_exc).__name__}: {last_exc}"
        if screenshot_path:
            msg += f"\nScreenshot: {screenshot_path}"

        raise TimeoutErrorWithScreenShot(msg, screenshot_path=screenshot_path)

    def until_not(
            self,
            predicate: Callable[[], bool],
            on_timeout: Callable[[], str],
            take_screenshot: Optional[Callable[[str], bool]] = None,
            ignored_exceptions: Optional[Iterable[Type[BaseException]]] = (NoSuchElementException,
                                                                           StaleElementReferenceException),
    ) -> bool:
        return self.until(lambda: not predicate(), on_timeout, take_screenshot, ignored_exceptions)
