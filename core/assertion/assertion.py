from __future__ import annotations

import json
from typing import Any, Callable, Iterable, Mapping, Optional

from core.logging.logging import Logger
from core.report.reporting import AllureReporter

# --- Optional: soft assertions via pytest-check ---
try:
    import pytest_check as check  # pip install pytest-check
    _SOFT_ASSERT = True
except ImportError:
    check = None
    _SOFT_ASSERT = False
    Logger.info("pytest-check not installed. Falling back to hard assertions (standard assert).")


def _attach_json_allure(title: str, data: Any) -> None:
    """Helper to attach JSON data to Allure report."""
    AllureReporter.attach_json(name=title, data=data, pretty=True)


def _fail(msg: str, expr: bool = False) -> None:
    """Uses pytest_check for soft assertion or standard assert for hard assertion."""
    if _SOFT_ASSERT:
        check.is_true(expr, msg)
    else:
        assert expr, msg


# ---------------------------
#          HELPER
# ---------------------------


def assert_equal(actual: Any, expected: Any, msg: Optional[str] = None) -> None:
    """Compare equal – with optional message."""
    if actual != expected:
        _attach_json_allure("Expected vs Actual", {"expected": expected, "actual": actual})
        _fail(msg or f"Values are not equal. Expected: {expected!r}, Actual: {actual!r}", expr=False)


def assert_true(expr: bool, msg: Optional[str] = None) -> None:
    """Assert that the expression is True."""
    if not expr:
        _fail(msg or "Expected condition to be True", expr=False)


def assert_false(expr: bool, msg: Optional[str] = None) -> None:
    """Assert that the expression is False."""
    if expr:
        _fail(msg or "Expected condition to be False", expr=False)


def assert_in(member: Any, container: Iterable[Any], msg: Optional[str] = None) -> None:
    """Assert that the member is in the container."""
    if member not in container:
        container_display = list(container) if not isinstance(container, (str, bytes)) else {"text": container}
        _attach_json_allure("Container", container_display)
        _fail(msg or f"{member!r} not found in container", expr=False)


def assert_not_in(member: Any, container: Iterable[Any], msg: Optional[str] = None) -> None:
    """Assert that the member is not in the container."""
    if member in container:
        _fail(msg or f"{member!r} unexpectedly found in container", expr=False)


def assert_len(obj: Any, expected_len: int, msg: Optional[str] = None) -> None:
    """Assert that the object has the expected length."""
    actual_len = len(obj)
    if actual_len != expected_len:
        _attach_json_allure("Length check", {"expected_len": expected_len, "actual_len": actual_len})
        _fail(msg or f"Length mismatch. Expected: {expected_len}, Actual: {actual_len}", expr=False)


def assert_between(num: float, lo: float, hi: float, inclusive: bool = True, msg: Optional[str] = None) -> None:
    """Assert that the number is within the specified range."""
    is_in_range = (lo <= num <= hi) if inclusive else (lo < num < hi)
    if not is_in_range:
        _attach_json_allure("Range", {"value": num, "lo": lo, "hi": hi, "inclusive": inclusive})
        _fail(msg or f"{num} not in range [{lo}, {hi}{']' if inclusive else ')'}]", expr=False)


def assert_json_contains(actual: Mapping[str, Any], expected_subset: Mapping[str, Any],
                         msg: Optional[str] = None) -> None:
    """Every key/value in expected_subset must be present in actual (simple deep comparison)."""
    missing_or_diff = {}
    for k, v in expected_subset.items():
        if k not in actual or actual[k] != v:
            missing_or_diff[k] = {"expected": v, "actual": actual.get(k, "<MISSING>")}

    if missing_or_diff:
        _attach_json_allure("JSON diff",
                            {"expected_subset": expected_subset, "actual": actual, "missing_or_diff": missing_or_diff})
        _fail(msg or "JSON does not contain expected subset", expr=False)


def assert_raises(fn: Callable, exc: type[BaseException], msg: Optional[str] = None) -> BaseException:
    """Expect the function to throw an exception; return the exception to continue asserting the property."""
    with pytest.raises(exc) as exc_info:
        fn()

    return exc_info.value
