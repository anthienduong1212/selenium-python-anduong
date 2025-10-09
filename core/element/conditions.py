from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement

import re

Predicate = Callable[[WebElement], bool]


@dataclass(frozen=True)
class Condition:
    name: str
    predicate: Predicate
    explain: Optional[Callable[[WebElement], str]] = None

    def test(self, el: WebElement) -> bool:
        try:
            return self.predicate(el)
        except StaleElementReferenceException:
            # stale -> failed, let Waiter try again
            return False


def appear() -> Condition:
    return visible()


def disappear() -> Condition:
    return hidden()


def visible() -> Condition:
    return Condition("visible", lambda e: e.is_displayed())


def hidden() -> Condition:
    return Condition("hidden", lambda e: not e.is_displayed())


def present() -> Condition:
    return Condition("present", lambda e: e is not None)


def enabled() -> Condition:
    return Condition("enabled", lambda e: e.is_enabled())


def disabled() -> Condition:
    return Condition("disabled", lambda e: not e.is_enabled())


def clickable() -> Condition:
    def _pred(e: WebElement) -> bool:
        return e.is_displayed() and e.is_enabled()

    return Condition("clickable", _pred)


def has_text(substr: str) -> Condition:
    return Condition(f'has_text("{substr}")', lambda e: substr in (e.text or ""))


def exact_text(text: str) -> Condition:
    return Condition(f'exact_text("{text}")', lambda e: (e.text or "") == text)


def value_is(text: str) -> Condition:
    return Condition(f'value_is("{text}")', lambda e: (e.get_attribute("value") or "") == text)


def attr(name: str, value: str | None = None) -> Condition:
    if value is None:
        return Condition(f'attr("{name}") exists', lambda e: e.get_attribute(name) is not None)
    return Condition(f'attr("{name}") == "{value}"', lambda e: (e.get_attribute(name) or "") == value)


def css_class(name: str) -> Condition:
    return Condition(f'css_class("{name}")', lambda e: name in (e.get_attribute("class") or "").split())


def selected() -> Condition:
    return Condition("selected", lambda e: e.is_selected())


def text_matches(pattern: str | re.Pattern) -> Condition:
    rx = re.compile(pattern) if isinstance(pattern, str) else pattern
    return Condition(f"text_matches({rx.pattern})", lambda e: bool(rx.search(e.text or "")))


def css_value(prop: str, value: str) -> Condition:
    return Condition(f'css_value("{prop}") == "{value}"', lambda e: (e.value_of_css_property(prop) or "") == value)


def attribute_contains(name: str, substring: str) -> Condition:
    return Condition(f'attr("{name}") contains "{substring}"', lambda e: substring in (e.get_attribute(name) or ""))


def not_(cond: Condition) -> Condition:
    return Condition(f"not({cond.name})", lambda e: not cond.predicate(e))


# Alias “should_be / should_have” style
be_visible = visible
be_hidden = hidden
be_enabled = enabled
be_disabled = disabled
be_clickable = clickable
have_text = has_text
have_exact_text = exact_text
have_value = value_is
have_attr = attr
have_css_class = css_class
be_selected = selected
