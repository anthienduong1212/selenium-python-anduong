from abc import ABC
from contextlib import contextmanager
from typing import Callable
import allure

from core.report.reporting import AllureReporter
from core.driver.driver_manager import DriverManager
from core.logging.logging import Logger
from core.assertion.assertions import AssertionInterface


class BaseAssertion(AssertionInterface, ABC):

    @classmethod
    @contextmanager
    def assertion_step(cls, description: str):
        with AllureReporter.step(description):
            try:
                yield
            finally:
                try:
                    AllureReporter.attach_page_screenshot(name=f"Screenshot for assertion: {description}")
                except Exception as e:
                    Logger.warning(f"Could not attach screenshot for assertion step: {e}")

    def assert_raises(self, fn: Callable, exc: type[BaseException]) -> BaseException:
        """Expect the function to throw an exception; return the exception to continue asserting the property."""
        with pytest.raises(exc) as exc_info:
            fn()
        return exc_info.value
