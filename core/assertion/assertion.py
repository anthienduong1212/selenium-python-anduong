from __future__ import annotations

import json
import allure
from typing import Any, Callable, Iterable, Mapping, Optional

from core.logging.logging import Logger
from core.report.reporting import AllureReporter


def _attach_json_allure(title: str, data: Any) -> None:
    """Helper to attach JSON data to Allure report."""
    AllureReporter.attach_json(name=title, data=data, pretty=True)


# ---------------------------
#          HELPER
# ---------------------------

def assert_equal(actual: Any, expected: Any, msg: str) -> None:
    """Compare equal"""
    description = f"{msg} | Expected: {expected!r}, Actual: {actual!r}"

    with AllureReporter.step(f"{description}"):
        _attach_json_allure("Expected vs Actual", {"expected": expected, "actual": actual})

        try:
            assert actual == expected, msg or f"Values are not equal. Expected: {expected!r}, Actual: {actual!r}"
            Logger.info(f"PASS: {description}")
        except AssertionError as e:
            Logger.error(f"FAIL: {description}")
            AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
            raise e


def assert_true(expr: bool, msg: str) -> None:
    """Assert that the expression is True."""
    description = f"{msg} |Condition: {expr}"

    with AllureReporter.step(f"Assert true: {description}"):
        try:
            assert expr, msg or "Expected condition to be True"
            Logger.info(f"PASS: {description}")
        except AssertionError as e:
            Logger.error(f"FAIL: {description}")
            AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
            raise e


def assert_false(expr: bool, msg: str) -> None:
    """Assert that the expression is False."""
    description = f"{msg} |Condition: {expr}"

    with AllureReporter.step(f"Assert false: {description}"):
        try:
            assert not expr, msg or "Expected condition to be False"
            Logger.info(f"PASS: {description}")
        except AssertionError as e:
            Logger.error(f"FAIL: {description}")
            AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
            raise e


def assert_in(member: Any, container: Iterable[Any], msg: str) -> None:
    """Assert that the member is in the container."""
    description = f"{msg} |{member!r} not found in container"

    with AllureReporter.step(f"{description}"):
        try:
            assert member in container, msg or f"{member!r} not found in container"
            Logger.info(f"PASS: {description}")
        except AssertionError as e:
            container_display = list(container) if not isinstance(container, (str, bytes)) else {"text": container}
            _attach_json_allure("Container", container_display)
            Logger.error(f"FAIL: {description}")
            AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
            raise e


def assert_not_in(member: Any, container: Iterable[Any], msg: str) -> None:
    """Assert that the member is not in the container."""
    description = f"{msg} |{member!r} unexpectedly found in container"

    with AllureReporter.step(f"Assert not in: {description}"):
        try:
            assert member not in container, msg or f"{member!r} unexpectedly found in container"
            Logger.info(f"PASS: {description}")
        except AssertionError as e:
            container_display = list(container) if not isinstance(container, (str, bytes)) else {"text": container}
            _attach_json_allure("Container", container_display)
            Logger.error(f"FAIL: {description}")
            AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
            raise e


def assert_len(obj: Any, expected_len: int, msg: str) -> None:
    """Assert that the object has the expected length."""
    actual_len = len(obj)
    description = f"{msg} |Length mismatch. Expected: {expected_len}, Actual: {actual_len}"

    with AllureReporter.step(f"Assert length: {description}"):
        try:
            assert actual_len == expected_len, msg or f"Length mismatch. Expected: {expected_len}, Actual: {actual_len}"
            Logger.info(f"PASS: {description}")
        except AssertionError as e:
            _attach_json_allure("Length check", {"expected_len": expected_len, "actual_len": actual_len})
            Logger.error(f"FAIL: {description}")
            AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
            raise e


def assert_between(num: float, lo: float, hi: float, inclusive: bool = True, msg: Optional[str] = None) -> None:
    """Assert that the number is within the specified range."""
    is_in_range = (lo <= num <= hi) if inclusive else (lo < num < hi)
    description = f"{msg} |{num} not in range [{lo}, {hi}{']' if inclusive else ')'}]"

    with AllureReporter.step(f"Assert between: {description}"):
        try:
            assert is_in_range, f"{msg} |{num} not in range [{lo}, {hi}{']' if inclusive else ')'}]"
            Logger.info(f"PASS: {description}")
        except AssertionError as e:
            _attach_json_allure("Range", {"value": num, "lo": lo, "hi": hi, "inclusive": inclusive})
            Logger.error(f"FAIL: {description}")
            AllureReporter.attach_page_screenshot(name="FAIL Screenshot")
            raise e


def assert_raises(fn: Callable, exc: type[BaseException]) -> BaseException:
    """Expect the function to throw an exception; return the exception to continue asserting the property."""
    with pytest.raises(exc) as exc_info:
        fn()
    return exc_info.value
