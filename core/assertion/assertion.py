from __future__ import annotations
from typing import Any, Iterable, Mapping, Optional, Callable
import json

from core.report.reporting import AllureReporter

# --- Optional: soft assertions via pytest-check ---
try:
    import pytest_check as check  # pip install pytest-check
except Exception:
    check = None


def _attach_json_allure(title: str, data: Any) -> None:
    AllureReporter.attach_json(name=title, data=data, pretty=True)


def _fail(msg: str) -> None:
    if check:
        check.is_true(False, msg)
    else:
        raise AssertionError(msg)


# ---------------------------
#          HELPER
# ---------------------------

def assert_equal(actual: Any, expected: Any, msg: Optional[str] = None) -> None:
    """Compare equal – with optional message."""
    if actual != expected:
        _attach_json_allure("Expected vs Actual", {"expected": expected, "actual": actual})
        _fail(msg or f"Expected == but got diff")


def assert_true(expr: bool, msg: Optional[str] = None) -> None:
    if not expr:
        _fail(msg or "Expected condition to be True")


def assert_false(expr: bool, msg: Optional[str] = None) -> None:
    if expr:
        _fail(msg or "Expected condition to be False")


def assert_in(member: Any, container: Iterable[Any], msg: Optional[str] = None) -> None:
    if member not in container:
        _attach_json_allure("Container",
                            list(container) if not isinstance(container, (str, bytes)) else {"text": container})
        _fail(msg or f"{member!r} not found in container")


def assert_not_in(member: Any, container: Iterable[Any], msg: Optional[str] = None) -> None:
    if member in container:
        _fail(msg or f"{member!r} unexpectedly found in container")


def assert_len(obj: Any, expected_len: int, msg: Optional[str] = None) -> None:
    try:
        n = len(obj)
    except Exception:
        _fail(msg or "Object has no len()")
        return
    if n != expected_len:
        _attach_json_allure("Length check", {"expected_len": expected_len, "actual_len": n})
        _fail(msg or f"len(obj) == {expected_len}, got {n}")


def assert_between(num: float, lo: float, hi: float, inclusive: bool = True, msg: Optional[str] = None) -> None:
    ok = (lo <= num <= hi) if inclusive else (lo < num < hi)
    if not ok:
        _attach_json_allure("Range", {"value": num, "lo": lo, "hi": hi, "inclusive": inclusive})
        _fail(msg or f"{num} not in range [{lo}, {hi}{']' if inclusive else ')'}]")


def assert_json_contains(actual: Mapping[str, Any], expected_subset: Mapping[str, Any],
                         msg: Optional[str] = None) -> None:
    """Every key/value in expected_subset must be present in actual (simple deep comparison)."""
    missing = {}
    for k, v in expected_subset.items():
        if k not in actual or actual[k] != v:
            missing[k] = {"expected": v, "actual": actual.get(k, "<MISSING>")}
    if missing:
        _attach_json_allure("JSON diff",
                            {"expected_subset": expected_subset, "actual": actual, "missing_or_diff": missing})
        _fail(msg or "JSON does not contain expected subset")


def assert_raises(fn: Callable, exc: type[BaseException], msg: Optional[str] = None) -> BaseException:
    """Expect the function to throw an exception; return the exception to continue asserting the property."""
    try:
        fn()
    except exc as e:
        return e
    except Exception as e:
        _attach_json_allure("Unexpected exception", {"type": type(e).__name__, "str": str(e)})
        _fail(msg or f"Expected {exc.__name__}, but got {type(e).__name__}")
    else:
        _fail(msg or f"Expected {exc.__name__} to be raised")
    return RuntimeError("unreachable")
