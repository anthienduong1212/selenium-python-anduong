from __future__ import annotations

import json
from abc import ABC

import allure
from typing import Any, Callable, Iterable, Mapping, Optional

from core.assertion.base_assertion import BaseAssertion
from core.logging.logging import Logger
from core.report.reporting import AllureReporter


def _attach_json_allure(title: str, data: Any) -> None:
    """Helper to attach JSON data to Allure report."""
    AllureReporter.attach_json(name=title, data=data, pretty=True)


class HardAsserts(BaseAssertion):
    def assert_equal(self, actual: Any, expected: Any, msg: str) -> None:
        """Compare equal"""

        description = f"{msg} | Expected: {expected!r}, Actual: {actual!r}"

        with self.assertion_step(f"Assert equal: {description}"):
            _attach_json_allure("Expected vs Actual", {"expected": expected, "actual": actual})

            try:
                assert actual == expected, description
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e

    def assert_true(self, expr: bool, msg: str) -> None:
        """Assert that the expression is True."""

        description = f"{msg} |Condition: {expr}"

        with self.assertion_step(f"Assert true: {description}"):
            try:
                assert expr, description
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e

    def assert_false(self, expr: bool, msg: str) -> None:
        """Assert that the expression is False."""

        description = f"{msg} |Condition: {expr}"

        with self.assertion_step(f"Assert false: {description}"):
            try:
                assert not expr, description
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e

    def assert_in(self, member: Any, container: Iterable[Any], msg: str) -> None:
        """Assert that the member is in the container."""

        description = f"{msg} |{member!r} not found in container"

        with self.assertion_step(f"{description}"):
            try:
                assert member in container, description
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                container_display = list(container) if not isinstance(container, (str, bytes)) else {"text": container}
                _attach_json_allure("Container", container_display)
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e

    def assert_not_in(self, member: Any, container: Iterable[Any], msg: str) -> None:
        """Assert that the member is not in the container."""

        description = f"{msg} |{member!r} unexpectedly found in container"

        with self.assertion_step(f"Assert not in: {description}"):
            try:
                assert member not in container, description
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                container_display = list(container) if not isinstance(container, (str, bytes)) else {"text": container}
                _attach_json_allure("Container", container_display)
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e

    def assert_len(self, obj: Any, expected_len: int, msg: str) -> None:
        """Assert that the object has the expected length."""

        actual_len = len(obj)
        description = f"{msg} | Expected: {expected_len}, Actual: {actual_len}"

        with self.assertion_step(f"Assert length: {description}"):
            try:
                assert actual_len == expected_len, description
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                _attach_json_allure("Length check", {"expected_len": expected_len, "actual_len": actual_len})
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e

    def assert_between(self, num: float, lo: float, hi: float, inclusive: bool = True, msg: Optional[str] = None) -> None:
        """Assert that the number is within the specified range."""

        is_in_range = (lo <= num <= hi) if inclusive else (lo < num < hi)
        description = f"{msg} |{num} not in range [{lo}, {hi}{']' if inclusive else ')'}]"

        with self.assertion_step(f"Assert between: {description}"):
            try:
                assert is_in_range, description
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                _attach_json_allure("Range", {"value": num, "lo": lo, "hi": hi, "inclusive": inclusive})
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e
