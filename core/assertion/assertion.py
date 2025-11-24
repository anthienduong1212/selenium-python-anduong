from __future__ import annotations

import json
import allure
from typing import Any, Callable, Iterable, Mapping, Optional

from core.logging.logging import Logger
from core.report.reporting import AllureReporter


def _attach_json_allure(title: str, data: Any) -> None:
    """Helper to attach JSON data to Allure report."""
    AllureReporter.attach_json(name=title, data=data, pretty=True)


def _fail(msg: str, expr: bool = False) -> None:
    """Uses pytest_check for soft assertion or standard assert for hard assertion."""
    if not expr:
        AllureReporter.attach_page_screenshot()
    assert expr, msg


# ---------------------------
#          HELPER
# ---------------------------

@allure.step("{msg} | EXPECTED is '{expected!r}', ACTUAL is '{actual!r}'")
def assert_equal(actual: Any, expected: Any, msg: str) -> None:
    """Compare equal"""
    if actual != expected:
        _attach_json_allure("Expected vs Actual", {"expected": expected, "actual": actual})

    _fail(msg or f"Values are not equal. Expected: {expected!r}, Actual: {actual!r}", expr=(actual == expected))


@allure.step("{msg}")
def assert_true(expr: bool, msg: str) -> None:
    """Assert that the expression is True."""
    _fail(msg or "Expected condition to be True", expr=expr)


@allure.step("{msg}")
def assert_false(expr: bool, msg: str) -> None:
    """Assert that the expression is False."""
    _fail(msg or "Expected condition to be False", expr=(not expr))


@allure.step("{msg}")
def assert_in(member: Any, container: Iterable[Any], msg: str) -> None:
    """Assert that the member is in the container."""
    if member not in container:
        container_display = list(container) if not isinstance(container, (str, bytes)) else {"text": container}
        _attach_json_allure("Container", container_display)

    _fail(msg or f"{member!r} not found in container", expr=(member in container))


@allure.step("{msg}")
def assert_not_in(member: Any, container: Iterable[Any], msg: str) -> None:
    """Assert that the member is not in the container."""
    if member in container:
        container_display = list(container) if not isinstance(container, (str, bytes)) else {"text" : container}
        _attach_json_allure("Container", container_display)

    _fail(msg or f"{member!r} unexpectedly found in container", expr=(member not in container))


@allure.step("{msg} | EXPECTED length is '{expected_len}'")
def assert_len(obj: Any, expected_len: int, msg: str) -> None:
    """Assert that the object has the expected length."""
    actual_len = len(obj)
    if actual_len != expected_len:
        _attach_json_allure("Length check", {"expected_len": expected_len, "actual_len": actual_len})

    _fail(msg or f"Length mismatch. Expected: {expected_len}, Actual: {actual_len}", expr=(actual_len == expected_len))


@allure.step("{msg}")
def assert_between(num: float, lo: float, hi: float, inclusive: bool = True, msg: Optional[str] = None) -> None:
    """Assert that the number is within the specified range."""
    is_in_range = (lo <= num <= hi) if inclusive else (lo < num < hi)
    if not is_in_range:
        _attach_json_allure("Range", {"value": num, "lo": lo, "hi": hi, "inclusive": inclusive})

    _fail(msg or f"{num} not in range [{lo}, {hi}{']' if inclusive else ')'}]", expr=is_in_range)


def assert_raises(fn: Callable, exc: type[BaseException]) -> BaseException:
    """Expect the function to throw an exception; return the exception to continue asserting the property."""
    with pytest.raises(exc) as exc_info:
        fn()
    return exc_info.value
