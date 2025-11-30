from __future__ import annotations

import json
from abc import ABC

import allure
from typing import Any, Callable, Iterable, Mapping, Optional

import pytest_check as soft_assert_check

from core.assertion.assertions import AssertionInterface
from core.logging.logging import Logger
from core.report.reporting import AllureReporter


class SoftAsserts(AssertionInterface, ABC):
    def assert_equal(self, actual: Any, expected: Any, msg: str) -> None:
        """Compare equal"""

        description = f"{msg} | Expected: {expected!r}, Actual: {actual!r}"

        with AllureReporter.step(f"{description}"):
            _attach_json_allure("Expected vs Actual", {"expected": expected, "actual": actual})

            try:
                soft_assert_check.is_true(actual == expected, description)
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e

    def assert_true(self, expr: bool, msg: str) -> None:
        """Assert that the expression is True."""

        description = f"{msg} |Condition: {expr}"

        with AllureReporter.step(f"Assert true: {description}"):
            try:
                soft_assert_check.is_true(expr, description)
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e

    def assert_false(self, expr: bool, msg: str) -> None:
        """Assert that the expression is False."""

        description = f"{msg} |Condition: {expr}"

        with AllureReporter.step(f"Assert false: {description}"):
            try:
                soft_assert_check.is_true(not expr, description)
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e

    def assert_in(self, member: Any, container: Iterable[Any], msg: str) -> None:
        """Assert that the member is in the container."""

        description = f"{msg} |{member!r} not found in container"

        with AllureReporter.step(f"{description}"):
            try:
                soft_assert_check.is_true(member in container, description)
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

        with AllureReporter.step(f"Assert not in: {description}"):
            try:
                soft_assert_check.is_true(member not in container, description)
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
        description = f"{msg} |Length mismatch. Expected: {expected_len}, Actual: {actual_len}"

        with AllureReporter.step(f"Assert length: {description}"):
            try:
                soft_assert_check.is_true(actual_len == expected_len, description)
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                _attach_json_allure("Length check", {"expected_len": expected_len, "actual_len": actual_len})
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e

    def assert_between(self, num: float, lo: float, hi: float, inclusive: bool = True,
                       msg: Optional[str] = None) -> None:
        """Assert that the number is within the specified range."""

        is_in_range = (lo <= num <= hi) if inclusive else (lo < num < hi)
        description = f"{msg} |{num} not in range [{lo}, {hi}{']' if inclusive else ')'}]"

        with AllureReporter.step(f"Assert between: {description}"):
            try:
                soft_assert_check.is_true(is_in_range, description)
                Logger.info(f"PASS: {description}")
            except AssertionError as e:
                _attach_json_allure("Range", {"value": num, "lo": lo, "hi": hi, "inclusive": inclusive})
                Logger.error(f"FAIL: {description}")
                AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
                raise e
