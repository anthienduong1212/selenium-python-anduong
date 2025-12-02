from __future__ import annotations

import json
from abc import ABC

import allure
from typing import Any, Callable, Iterable, Mapping, Optional

import pytest_check as soft_assert_check

from core.assertion.base_assertion import BaseAssertion
from core.logging.logging import Logger
from core.report.reporting import AllureReporter


class SoftAsserts(BaseAssertion):
    def assert_equal(self, actual: Any, expected: Any, msg: str) -> None:
        """Compare equal"""

        description = f"{msg} | Expected: {expected!r}, Actual: {actual!r}"

        with self.assertion_step(f"{description}"):
            _attach_json_allure("Expected vs Actual", {"expected": expected, "actual": actual})

            result = soft_assert_check.equal(actual == expected, description)
            if result:
                Logger.info(f"PASS: {description}")
                AllureReporter.attach_text("Soft Checkpoint PASSED", f"{actual} == {expected}")
            else:
                Logger.error(f"FAIL: {description}")

    def assert_true(self, expr: bool, msg: str) -> None:
        """Assert that the expression is True."""

        description = f"{msg} |Condition: {expr}"

        with self.assertion_step(f"Assert true: {description}"):
            result = soft_assert_check.is_true(expr, description)
            if result:
                Logger.info(f"PASS: {description}")
                AllureReporter.attach_text("Soft Checkpoint PASSED", f"Expected TRUE")
            else:
                Logger.error(f"FAIL: {description}")

    def assert_false(self, expr: bool, msg: str) -> None:
        """Assert that the expression is False."""

        description = f"{msg} |Condition: {expr}"

        with self.assertion_step(f"Assert false: {description}"):
            result = soft_assert_check.is_false(not expr, description)
            if result:
                Logger.info(f"PASS: {description}")
                AllureReporter.attach_text("Soft Checkpoint PASSED", f"Expected FALSE")
            else:
                Logger.error(f"FAIL: {description}")

    def assert_in(self, member: Any, container: Iterable[Any], msg: str) -> None:
        """Assert that the member is in the container."""

        description = f"{msg} |{member!r} found in container"

        with self.assertion_step(f"{description}"):
            result = soft_assert_check.is_in(member in container, description)
            container_display = list(container) if not isinstance(container, (str, bytes)) else {"text": container}
            _attach_json_allure("Container", container_display)

            if result:
                Logger.info(f"PASS: {description}")
            else:
                Logger.error(f"FAIL: {description}")

    def assert_not_in(self, member: Any, container: Iterable[Any], msg: str) -> None:
        """Assert that the member is not in the container."""

        description = f"{msg} |{member!r} unexpectedly found in container"

        with self.assertion_step(f"Assert not in: {description}"):
            result = soft_assert_check.is_not_in(member not in container, description)
            container_display = list(container) if not isinstance(container, (str, bytes)) else {"text": container}
            _attach_json_allure("Container", container_display)

            if result:
                Logger.info(f"PASS: {description}")
            else:
                Logger.error(f"FAIL: {description}")

    def assert_len(self, obj: Any, expected_len: int, msg: str) -> None:
        """Assert that the object has the expected length."""

        actual_len = len(obj)
        description = f"{msg} |Length mismatch. Expected: {expected_len}, Actual: {actual_len}"
        _attach_json_allure("Length check", {"expected_len": expected_len, "actual_len": actual_len})

        with self.assertion_step(f"Assert length: {description}"):
            result = soft_assert_check.is_true(actual_len == expected_len, description)
            if result:
                Logger.info(f"PASS: {description}")
                AllureReporter.attach_text("Soft checkpoint PASSED")
            else:
                Logger.error(f"FAIL: {description}")

    def assert_between(self, num: float, lo: float, hi: float, inclusive: bool = True,
                       msg: Optional[str] = None) -> None:
        """Assert that the number is within the specified range."""

        is_in_range = (lo <= num <= hi) if inclusive else (lo < num < hi)
        description = f"{msg} |{num} not in range [{lo}, {hi}{']' if inclusive else ')'}]"
        _attach_json_allure("Range", {"value": num, "lo": lo, "hi": hi, "inclusive": inclusive})

        with self.assertion_step(f"Assert between: {description}"):
            result = soft_assert_check.is_true(is_in_range, description)
            if result:
                Logger.info(f"PASS: {description}")
            else:
                Logger.error(f"FAIL: {description}")
