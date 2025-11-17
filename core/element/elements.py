from __future__ import annotations

import time
from dataclasses import replace
from typing import List, Optional, Union

from selenium.common.exceptions import (ElementClickInterceptedException,
                                        JavascriptException,
                                        NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver, WebElement

from core.configuration.configuration import Configuration
from core.driver.driver_manager import DriverManager
from core.element.conditions import Condition, click_ready, in_viewport
from core.element.conditions import visible as cond_visible
from core.element.locators import Locator
from core.logging.logging import Logger
from core.report.reporting import AllureReporter
from core.waiter.wait import Waiter


class Element:
    """
     - lazy locating (find if you need)
     - auto-wait with .should(...)
     - fluent API: .click().type("...").should(be_visible())
     - context-find: parent.find("child")
   """

    def __init__(self,
                 selector: Locator,
                 config: Optional[Configuration] = None,
                 context: Optional["Element"] = None):

        if not isinstance(selector, Locator):
            raise TypeError(f"Selector must be a Locator object"
                            f", not {type(selector).__name__}. Ensure Locator is used for initialization.")

        self.locator: Locator = selector
        self.locator: Locator = selector
        self.config: Configuration = config or DriverManager.get_current_config()
        self.context: Optional["Element"] = context
        self.name = str(self.locator)
        self._last_ref: Optional[WebElement] = None

        self.waiter = Waiter(
            timeout_s=self.config.wait_timeout_ms / 1000.0,
            poll_s=self.config.polling_interval_ms / 1000.0,
        )

    # ================================
    #          DRIVER/LOCATING
    # ================================

    def _driver(self) -> WebDriver:
        """Get the current WebDriver instance."""
        return DriverManager.get_driver(self.config)

    def _find_web_element_in_context(self, locator: Locator) -> WebElement:
        """
        Context-aware resolve:
        - If locator has parent -> resolve parent and find in CONTEXT parent
        - If not -> find from driver
        """
        if locator.parent:
            parent_we = self._find_web_element_in_context(locator.parent)
            return parent_we.find_element(locator.by, locator.value)

        return self._driver().find_element(locator.by, locator.value)

    def _find_now(self) -> WebElement:
        """Find the element on the page immediately."""
        current_loc = self.locator

        if self.context and not current_loc.parent:
            current_loc = replace(current_loc, parent=self.context.locator)

        return self._find_web_element_in_context(current_loc)

    def _resolve(self):
        """
        Resolve the WebElement reference, re-finding if stale.
        This is the core lazy-loading mechanism.
        """
        if self._last_ref is not None:
            try:
                _ = self._last_ref.is_enabled()
                return self._last_ref
            except StaleElementReferenceException:
                Logger.debug(f"Element {self.name} is stale. Re-finding.")
                self._last_ref = None
            except NoSuchElementException:
                Logger.debug(f"Element {self.name} disappeared. Re-finding.")
                self._last_ref = None

        self._last_ref = self._find_now()
        return self._last_ref

    # ================================
    #          COMPOSITION
    # ================================

    def find(self, selector: Locator) -> "Element":
        """Find a single child element within this element's context."""
        return Element(selector, config=self.config, context=self)

    def all(self, selector: Locator) -> "Elements":
        """Find all child elements within this element's context."""
        return Elements(selector, config=self.config, context=self)

    # ================================
    #          SCROLLING
    # ================================

    def is_in_viewport(self) -> bool:
        """
        Check if the element is currently visible within the browser viewport
        using the shared condition from conditions.py.
        """
        viewport_cond = in_viewport()
        try:
            return viewport_cond.predicate(self._resolve())
        except StaleElementReferenceException:
            return viewport_condition.predicate(self._find_now())
        except Exception as e:
            Logger.error(f"Error checking viewport status for {self.name}: {e}")
            return False

    def scroll_into_view(self):
        """Scroll the element into the visible part of the screen."""
        if self.is_in_viewport():
            return

        el = self._resolve()
        backend = getattr(self.config, "scroll_backend", "js")
        block = getattr(self.config, "scroll_block", "center")
        header_offset = getattr(self.config, "header_offset_px", 0)

        try:
            if backend == "wheel":
                ActionChains(self._driver()).scroll_to_element(el).perform()
            elif backend == "move":
                ActionChains(self._driver()).move_to_element(el).perform()
            else:
                self._driver().execute_script(
                    "arguments[0].scrollIntoView({block: arguments[1], inline: 'nearest'});",
                    el, block
                )
            if header_offset:
                self._driver().execute_script("window.scrollBy(0, -arguments[0]);", header_offset)
        except Exception as e:
            Logger.warning(f"Scroll backend failed: {e}. Trying simple move_to_element.")
            try:
                ActionChains(self._driver()).move_to_element(el).perform()
            except Exception as e_fallback:
                Logger.error(f"All scrolling methods failed: {e_fallback}")
                pass

        # Avoid jitter
        t0 = time.time()
        last_top = None
        while time.time() < t0 + 0.5:
            try:
                top = self._driver().execute_script("return arguments[0].getBoundingClientRect().top;", el)
            except Exception:
                break
            if last_top is not None and abs(top - last_top) < 0.5:
                break
            last_top = top
            time.sleep(0.05)

    # ================================
    #          ACTIONS
    # ================================

    def click(self) -> "Element":
        """Click on the element."""
        self.should(cond_visible())
        try:
            self._resolve().click()
        except ElementClickInterceptedException:
            Logger.info(f"Click intercepted. Waiting for click ability on {self.name}.")
            timeout_ms = max(500, self.config.polling_interval_ms * 4)
            self.should(click_ready(), timeout_ms=timeout_ms)
            self._resolve().click()
        return self

    def type(self, text: str, clear: bool = True) -> "Element":
        """Type text into an input element."""
        self.should(cond_visible())
        el = self._resolve()
        if clear:
            try:
                el.clear()
            except Exception:
                Logger.debug(f"el.clear() failed for {self.name}: {e}. Falling back to Ctrl+A+Delete.")
                el.send_keys(Keys.CONTROL, "a")
                el.send_keys(Keys.DELETE)
        el.send_keys(text)
        return self

    def press(self, *keys) -> "Element":
        """Send specific key presses to the element (e.g., Keys. ENTER)."""
        self._resolve().send_keys(*keys)
        return self

    def clear(self) -> "Element":
        """Clear the text of an input element."""
        self._resolve().clear()
        return self

    def hover(self) -> "Element":
        """Clear the text of an input element."""
        self.should(cond_visible())
        self.scroll_into_view()
        ActionChains(self._driver()).move_to_element(self._resolve()).perform()
        return self

    # ================================
    #          STATE GETTERS
    # ================================

    def text(self, mode: str = "visible") -> str:
        """
        :param mode:
            - "visible": same as user see; prior .text, fallback innerText
            - "all": get all text in DOM; using textContent
            - "value": for input/textarea; using value
        """
        el = self._resolve()
        try:
            if mode == "visible":
                return (el.text or el.get_attribute("innerText") or "").strip()
            elif mode == "all":
                return (el.get_attribute("textContent") or "").strip()
            elif mode == "value":
                return (el.get_property("value") or el.get_attribute("value") or "").strip()
            else:
                return (el.text or el.get_attribute("innerText") or "").strip()
        except StaleElementReferenceException:
            Logger.warning("StaleElementReferenceException in text() getter.")
            return self.text(mode=mode)
        except Exception as e:
            Logger.error(f"Error getting text in mode {mode}: {e}")
            return ""

    def attr(self, name: str) -> Optional[str]:
        """Get attribute value of the element."""
        try:
            return self._resolve().get_attribute(name)
        except Exception as e:
            Logger.error(f"Error getting attribute {name}: {e}")
            return None

    def css(self, name: str) -> Optional[str]:
        """Get CSS property value of the element."""
        try:
            return self._resolve().value_of_css_property(name)
        except Exception as e:
            Logger.error(f"Error getting CSS property {name}: {e}")
            return None

    # ================================
    #          ELEMENT UTILS
    # ================================

    def highlight(self, style: str = "border: 3px solid red;", duration_ms: int = 200) -> None:
        """Highlight the element temporarily for debugging."""
        try:
            el = self._resolve()
            prev = self._driver().execute_script("return arguments[0].getAttribute('style')||'';", el) or ""
            self._driver().execute_script(
                "arguments[0].setAttribute('style', (arguments[1] ? arguments[1]+';' : '') + arguments[2]);",
                el, prev, style
            )
            time.sleep(max(0, duration_ms) / 1000.0)
            self._driver().execute_script("arguments[0].setAttribute('style', arguments[1]);", el, prev)
        except Exception as e:
            Logger.warning(f"Highlight failed: {e}")
            pass

    def exists(self) -> bool:
        """Check if the element exists in the DOM without waiting."""
        try:
            if self.context:
                p = self.context._resolve()
                return len(p.find_elements(self.locator.by, self.locator.value)) > 0
            return len(self._driver().find_elements(self.locator.by, self.locator.value)) > 0
        except Exception:
            return False

    # ================================
    #      Waiting / Assertions
    # ================================

    def should(self, *conditions: Condition, timeout_ms: Optional[int] = None) -> "Element":
        """Wait until a specific condition is met for the element."""
        timeout_s = timeout_ms / 1000.0 if timeout_ms else self.waiter.timeout_s

        assert timeout_s > 0, "Timeout for 'should' condition must be greater than zero."

        if not conditions:
            return self

        temp_wait = self.waiter
        if timeout_ms is not None:
            temp_wait = Waiter(timeout_s=timeout_s,
                               poll_s=self.waiter.poll_s)

        desc = f'Element("{self.name}") should meet: ' + ", ".join(c.name for c in conditions)

        def _condition_checker() -> bool:
            """Closure that runs all conditions, handling stale elements."""
            try:
                el = self._resolve()
                return all(c.predicate(el) for c in conditions)
            except (NoSuchElementException, StaleElementReferenceException):
                return False

        def _on_timeout() -> str:
            Logger.info("Condition was not met within the timeout period.")
            snapshot = "<not present>"
            try:
                el = self._find_now()
                snapshot = f'text="{(el.text or "").strip()}", enabled={el.is_enabled()}, displayed={el.is_displayed()}'
            except Exception:
                pass
            return f"{desc}. Last state: {snapshot}. Locator={self.locator}"

        def _shot(path: str) -> bool:
            Logger.info(f"Attempting to take a screenshot at: {path}")
            try:
                return self._driver().save_screenshot(path)
            except Exception:
                return False

        with AllureReporter.step(desc):
            try:
                temp_wait.until(_condition_checker, _on_timeout)
                return self
            except TimeoutException as e:
                spath = getattr(e, "screenshot_path", None)
                if spath:
                    AllureReporter.attach_file(spath, f"FAILED - {self.name}", "image/png")
                AllureReporter.attach_text("Locator", str(self.locator))
                raise

    def should_be(self, *conditions: Condition, timeout_ms: Optional[int] = None) -> "Element":
        return self.should(*conditions, timeout_ms=timeout_ms)

    # ================================
    #              WITH
    # ================================
    def _with(self, **overrides) -> "Element":
        """Create a copy of Element with config override."""
        new_cfg = self.config.clone(**overrides)
        return Element(self.locator, config=new_cfg, context=self.context)

    def as_(self, name: str) -> "Element":
        """Assign a human-readable name to the element."""
        return Element(self.locator.with_decs(name), config=self.config, context=self.context)

# ================================
#          ELEMENTS COLLECTION
# ================================


class Elements:
    """
    Element Collection.
    Lazy: find_elements needed, support filter/map/first/get/size + should_have_size.
    """

    def __init__(self, selector: Locator,
                 config: Optional[Configuration] = None,
                 context: Element | None = None):

        if not isinstance(selector, Locator):
            raise TypeError(f"Selector must be a Locator object, not {type(selector).__name__}.")

        self.locator = selector
        self.config: Configuration = config or DriverManager.get_current_config()
        self.context = context
        self.name = str(self.locator)

        self.waiter = Waiter(
            timeout_s=self.config.wait_timeout_ms / 1000.0,
            poll_s=self.config.polling_interval_ms / 1000.0,
        )

    def _driver(self) -> WebDriver:
        return DriverManager.get_driver(self.config)

    def _resolve(self) -> List[WebElement]:
        """Find the list of WebElements immediately."""
        try:
            if self.context:
                parent = self.context._resolve()
                return parent.find_elements(self.locator.by, self.locator.value)
            return self._driver().find_elements(self.locator.by, self.locator.value)
        except (NoSuchElementException, StaleElementReferenceException):
            return []

    def first(self) -> Element:
        return self.get(0)

    def get(self, index: int) -> Element:
        """Get a specific element from the collection by index (lazily)."""
        if self.locator.by.lower() == "xpath":
            new_xpath_value = f"({self.locator.value})[{index + 1}]"
            new_locator = Locator(by="xpath", value=new_xpath_value, parent=self.locator.parent)
            return Element(new_locator,
                           config=self.config,
                           context=self.context)
        return IndexedElement(self, index)

    def size(self) -> int:
        """Get the current size of the collection."""
        return len(self._resolve())

    def texts(self) -> List[str]:
        """Get the visible text of all elements in the collection."""
        values: List[str] = []
        for el in self._resolve():
            try:
                values.append((el.text or "").strip())
            except StaleElementReferenceException:
                Logger.debug("Ignoring stale element in texts() collection.")
                continue
        return values

    def should_have_size(self, n: int, timeout_ms: Optional[int] = None) -> "Elements":
        """Wait until the collection has exactly the expected size."""
        timeout_s = timeout_ms/1000.0 if timeout_ms is not None else self.waiter.timeout_s

        temp_waiter = self.waiter
        if timeout_ms is not None:
            temp_waiter = Waiter(timeout_s=timeout_s, poll_s=self.waiter.poll_s)

        def _supplier() -> bool:
            return len(self._resolve()) == n

        def _on_timeout() -> str:
            actual = len(self._resolve())
            return f'Elements("{self.name}") expected size={n}, actual={actual}. Locator={self.locator}'

        def _shot(path: str) -> bool:
            try:
                return self._driver().save_screenshot(path)
            except Exception:
                return False

        with AllureReporter.step(f'Elements("{self.name}") should have size {n}'):
            try:
                temp_waiter.until(_supplier, _on_timeout)
                return self
            except TimeoutException as e:
                spath = getattr(e, "screenshot_path", None)
                if spath:
                    AllureReporter.attach_file(spath, f"FAILED - {self.name}", "image/png")
                AllureReporter.attach_text("Locator", str(self.locator))
                raise


class IndexedElement(Element):
    """
    Proxy an element in the collection by index (re-find each time to avoid staleness).
    """

    def __init__(self, collection: Elements, index: int):
        super().__init__(collection.locator, config=collection.config, context=collection.context)
        self._collection = collection
        self._index = index

    def _find_now(self) -> WebElement:
        els = self._collection._resolve()
        if self._index < 0 or self._index >= len(els):
            raise NoSuchElementException(
                f"Index {self._index} is out of range (size={len(els)}) for {self._collection.name}")
        return els[self._index]
