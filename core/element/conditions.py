from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement

from core.constants.JS_scripts import JSScript
from core.logging.logging import Logger

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


def in_viewport() -> Condition:
    """Check if element has dimension > 0 and locate in center of viewport"""

    def _pred(e: WebElement) -> bool:
        try:
            drv = e.parent
            rect = drv.execute_script(JSScript.GET_ELEMENT_RECT_SCRIPT, e)
            if rect["w"] <= 0 or rect["h"] <= 0:
                return False
            vw, vh = drv.execute_script(JSScript.GET_VIEWPORT_SIZE_SCRIPT)
            return 0 <= rect["cx"] < vw and 0 <= rect["cy"] < vh
        except Exception:
            Logger.debug("Element is not located in view port")
            return False

    return Condition("in_viewport", _pred)


def not_covered() -> Condition:
    """
    Checks if the top element at the center of the target element is the element itself
    or one of its descendants (meaning it's not blocked by an overlay).
    """

    def _pred(e: WebElement) -> bool:
        try:
            drv = e.parent
            cx, cy = drv.execute_script(JSScript.CENTER_COORDS_SCRIPT, e)
            top_el = drv.execute_script(JSScript.TOP_EL_SCRIPT, cx, cy)

            return top_el == e or drv.execute_script(JSScript.IS_DESCENDANT_SCRIPT, e, top_el)
        except Exception:
            Logger.debug("Element no longer attached to DOM")
            return False

    return Condition("not_covered", _pred)


def click_ready() -> Condition:
    # “clickable++”: visible + enabled + in_viewport + not_covered
    def _pred(e: WebElement) -> bool:
        try:
            if not e.is_displayed() or not e.is_enabled():
                return False
        except Exception:
            return False
        return in_viewport().predicate(e) and not_covered().predicate(e)

    return Condition("click_ready", _pred)


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
