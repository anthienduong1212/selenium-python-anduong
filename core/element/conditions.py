from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional, Union

from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from core.constants.JS_scripts import JSScript
from core.element.locator import Locator
from core.logging.logging import Logger

ECPredicate = Callable[[WebDriver], Union[bool, WebElement, object]]


@dataclass(frozen=True)
class Condition:
    name: str
    predicate: Optional[ECPredicate] = None
    ec_builder: Optional[Callable[[tuple[str, str]], ECPredicate]] = None

    def finalize(self, locator: tuple[str, str]):
        if self.ec_builder and not self.predicate:
            finalize_pred = self.ec_builder(locator)

            return Condition(
                name=self.name,
                predicate=finalize_pred,
                ec_builder=None
            )
        return self

    def __call__(self, driver: WebDriver) -> bool:
        if self.predicate:
            result = self.predicate(driver)
            return result is not None and result is not False
        raise RuntimeError("Condition was not finalized with a locator before use.")


def appear() -> Condition:
    return visible()


def disappear() -> Condition:
    return hidden()


def visible() -> Condition:
    return Condition("visible",
                     ec_builder=lambda loc: EC.visibility_of_element_located(loc))


def hidden() -> Condition:
    return Condition("hidden",
                     ec_builder=lambda loc: EC.invisibility_of_element_located(loc))


def present() -> Condition:
    return Condition("present",
                     ec_builder=lambda loc: EC.presence_of_element_located(loc))


def clickable() -> Condition:
    return Condition("clickable",
                     ec_builder=lambda loc: EC.element_to_be_clickable(loc))


def has_text(substr: str) -> Condition:
    return Condition(f'has_text("{substr}")',
                     ec_builder=lambda loc: EC.text_to_be_present_in_element(loc, substr))


def value_is(text: str) -> Condition:
    return Condition(f'value_is("{text}")',
                     ec_builder=lambda loc: EC.text_to_be_present_in_element_value(loc, text))


def selected() -> Condition:
    return Condition("selected",
                     ec_builder=lambda loc: EC.element_to_be_selected(loc))


def frame_display() -> Condition:
    return Condition("frame display",
                     ec_builder=lambda loc: EC.frame_to_be_available_and_switch_to_it(loc))


def _js_predicate_builder(element_predicate: Callable[[WebElement], bool]) \
        -> Callable[[tuple[str, str]], ECPredicate]:
    def builder(locator_tuple: tuple[str, str]) -> ECPredicate:
        def resolve_predicate(driver: WebDriver) -> bool:
            try:
                el = EC.visibility_of_element_located(locator_tuple)(driver)

                if el is None or el is False:
                    return False

                return element_predicate(el)

            except (NoSuchElementException, StaleElementReferenceException):
                return False
            except Exception as e:
                Logger.debug(f"Error in _js_predicate_builder() for locator {locator_tuple}: {e}")
                return False

        return resolve_predicate

    return builder


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

    return Condition("in_viewport", ec_builder=_js_predicate_builder(_pred))


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

    return Condition("not_covered", ec_builder=_js_predicate_builder(_pred))


def click_ready() -> Condition:
    return Condition(
        name="click_ready",
        ec_builder=lambda loc_tuple: EC.element_to_be_clickable(loc_tuple)
    )


# Alias “should_be / should_have” style
be_visible = visible
be_hidden = hidden
be_clickable = clickable
have_text = has_text
have_value = value_is
be_selected = selected
