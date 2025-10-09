from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import re
from selenium.webdriver.remote.webdriver import WebDriver


@dataclass(frozen=True)
class DriverCondition:
    name: str
    predicate: Callable[[WebDriver], bool]


def url_contain(substr: str) -> DriverCondition:
    return DriverCondition(f'url_contains("{substr}")', lambda d: substr in (d.current_url or ""))


def url_matches(pattern: str | re.Pattern) -> DriverCondition:
    rx = re.compile(pattern) if isinstance(pattern, str) else pattern
    return DriverCondition(f"url_matches({rx.pattern})", lambda d: bool(rx.search(d.current_url or "")))


def title_is(text: str) -> DriverCondition:
    return DriverCondition(f'title is("{text}")', lambda d: (d.title or "") == text)


def title_contains(substr: str) -> DriverCondition:
    return DriverCondition(f'title_contains("{substr}")', lambda d: substr in (d.title or ""))


