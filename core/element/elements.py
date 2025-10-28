from __future__ import annotations
import time
from typing import Optional, List, Union
from dataclasses import replace
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    JavascriptException
)

from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from core.element.locators import Locator
from core.waiter.wait import Waiter
from core.element.conditions import Condition, visible as cond_visible, click_ready
from core.report.reporting import AllureReporter

try:
    import allure
except Exception:
    allure = None

from core.driver.driver_manager import DriverManager
from core.configuration.configuration import Configuration


# ================================
#            HELPER
# ================================

def _resolve_selector(selector: Union[str, tuple, Locator]) -> Locator:
    return Locator.from_any(selector)


class Element:
    """
     - lazy locating (find if need)
     - auto-wait with .should(...)
     - fluent API: .click().type("...").should(be_visible())
     - context-find: parent.find("child")
   """

    def __init__(self, selector,
                 config: Optional[Configuration] = None,
                 context: Optional["Element"] = None
                 , name: [Optional] = None):

        self.locator: Locator = _resolve_selector(selector)
        self.config: Configuration = config or DriverManager.get_current_config()
        self.context: Optional["Element"] = context
        self.name = name or str(self.locator)
        self._last_ref: Optional[WebElement] = None

        self.waiter = Waiter(
            timeout_s=max(0.001, self.config.wait_timeout_ms / 1000.0),
            poll_s=max(0.001, self.config.polling_interval_ms / 1000.0),
        )

    # ================================
    #          DRIVER/LOCATING
    # ================================

    def _driver(self) -> WebDriver:
        return DriverManager.get_driver(self.config)

    def resolve_we(self, locator) -> WebElement:
        """
        Context-aware resolve:
        - If locator has parent -> resolve parent and find in CONTEXT parent
        - If not -> find from driver
        """
        if getattr(locator, "parent", None):
            parent_we = self.resolve_we(locator.parent)
            return parent_we.find_element(locator.by, locator.value)
        return self._driver().find_element(locator.by, locator.value)

    def _find_now(self) -> WebElement:
        loc = self.locator
        # If Element has context but locator doesn't have parent -> graft parent from context
        if self.context and not getattr(loc, "parent", None):
            loc = replace(loc, parent=self.context.locator)
        return self.resolve_we(loc)

    def _resolve(self):
        if self._last_ref is not None:
            try:
                _ = self._last_ref.is_enabled()
                return self._last_ref
            except StaleElementReferenceException:
                self._last_ref = None
        self._last_ref = self._find_now()

        return self._last_ref

    # ================================
    #          COMPOSITION
    # ================================

    def find(self, selector: Union[str, tuple, Locator], name: Optional[str] = None) -> "Element":
        return Element(selector, config=self.config, context=self, name=name)

    def all(self, selector: Union[str, tuple, Locator], name: Optional[str] = None) -> "Elements":
        return Elements(selector, config=self.config, context=self, name=name)

    # ================================
    #          SCROLLING
    # ================================

    def is_in_viewport(self) -> bool:
        try:
            return self._driver().execute_script(
                """
                    const r = arguments[0].getBoundingClientRect();
                    const vh = window.innerHeight || document.documentElement.clientHeight;
                    const vw = window.innerWidth  || document.documentElement.clientWidth;
                    return r.top >= 0 && r.left >= 0 && r.bottom <= vh && r.right <= vw;
                    """,
                self._resolve()
            )
        except JavascriptException:
            return True
        except Exception:
            return False

    def scroll_into_view(self):
        el = self._resolve()
        if self.is_in_viewport():
            return

        backend = getattr(self.config, "scroll_backend", "js")
        block = getattr(self.config, "scroll_block", "center")
        header_offset = getattr(self.config, "header_offset_px", 0)

        try:
            if backend == "wheel":
                ActionChains(self._driver()).scroll_to_element(el).perform()  # Selenium 4 wheel
            elif backend == "move":
                ActionChains(self._driver()).move_to_element(el).perform()
            else:
                self._driver().execute_script(
                    "arguments[0].scrollIntoView({block: arguments[1], inline: 'nearest'});",
                    el, block
                )
            if header_offset:
                self._driver().execute_script("window.scrollBy(0, -arguments[0]);", header_offset)
        except Exception:
            try:
                ActionChains(self._driver()).move_to_element(el).perform()
            except Exception:
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
        self.should(cond_visible())
        try:
            self._resolve().click()
        except ElementClickInterceptedException:
            self.should(click_ready(), timeout_ms=max(500, self.config.polling_interval_ms * 4))
            self._resolve().click()
        return self

    def type(self, text: str, clear: bool = True) -> "Element":
        self.should(cond_visible())
        self.scroll_into_view()
        el = self._resolve()
        if clear:
            try:
                el.clear()
            except Exception:
                el.send_keys(Keys.CONTROL, "a", Keys.DELETE)
        el.send_keys(text)
        return self

    def press(self, *keys) -> "Element":
        self._resolve().send_keys(*keys)
        return self

    def clear(self) -> "Element":
        self._resolve().clear()
        return self

    def hover(self) -> "Element":
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
        except Exception:
            return ""

    def attr(self, name: str) -> Optional[str]:
        try:
            return self._resolve().get_attribute(name)
        except Exception:
            return None

    def css(self, name: str) -> Optional[str]:
        try:
            return self._resolve().value_of_css_property(name)
        except Exception:
            return None

    # ================================
    #          ELEMENT UTILS
    # ================================

    def highlight(self, el: WebElement, style: str, duration_ms: int = 200) -> None:
        try:
            prev = self._driver().execute_script("return arguments[0].getAttribute('style')||'';", el) or ""
            self._driver().execute_script(
                "arguments[0].setAttribute('style', (arguments[1] ? arguments[1]+';' : '') + arguments[2]);",
                el, prev, style
            )
            time.sleep(max(0, duration_ms) / 1000.0)
            self._driver().execute_script("arguments[0].setAttribute('style', arguments[1]);", el, prev)
        except Exception:
            pass

    def exists(self) -> bool:
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
        if not conditions:
            return self

        orig_timeout = self.waiter.timeout_s
        if timeout_ms is not None:
            self.waiter.timeout_s = max(0.001, timeout_ms / 1000.0)

        desc = f'Element("{self.name}") should: ' + ", ".join(c.name for c in conditions)

        def _supplier() -> bool:
            try:
                el = self._resolve()
            except (NoSuchElementException, StaleElementReferenceException):
                # If element is not found or stale, continue waiting
                return False

            try:
                # Verify all conditions on found element
                return all(c.test(el) for c in conditions)
            except StaleElementReferenceException:
                return False

        def _on_timeout() -> str:
            # On time out, record the last state (or not found issue)
            try:
                el = self._resolve()
                snapshot = f'text="{(el.text or "").strip()}", enabled={el.is_enabled()}, displayed={el.is_displayed()}'
            except Exception as e:
                snapshot = f"<not present> ({type(e).__name__})"
            return f"{desc}. Last state: {snapshot}. Locator={self.locator}"

        def _shot(path: str) -> bool:
            try:
                return self._driver().save_screenshot(path)
            except Exception:
                return False

        with AllureReporter.step(desc):
            try:
                self.waiter.until(_supplier, _on_timeout, _shot)
                return self
            except Exception as e:
                # Attach information about failure (screenshot, locator)
                spath = getattr(e, "screenshot_path", None)
                if spath:
                    AllureReporter.attach_file(spath, f"FAILED - {self.name}", "image/png")
                AllureReporter.attach_text("Locator", str(self.locator))
                raise
            finally:
                self.waiter.timeout_s = orig_timeout

    def should_be(self, *conditions: Condition, timeout_ms: Optional[int] = None) -> "Element":
        return self.should(*conditions, timeout_ms=timeout_ms)

    def should_have(self, *conditions: Condition, timeout_ms: Optional[int] = None) -> "Element":
        return self.should(*conditions, timeout_ms=timeout_ms)

    # ================================
    #              WITH
    # ================================
    def _with(self, **overrides) -> "Element":
        """
            Create a copy of Element with config override
        """
        new_cfg = self.config.clone(**overrides)
        return Element(self.locator, config=new_cfg, context=self.context, name=self.name)

    def as_(self, name: str) -> "Element":
        return Element(self.locator.with_decs(name), config=self.config, context=self.context, name=name)


class Elements:
    """
    Element Collection.
    Lazy: find_elements needed, support filter/map/first/get/size + should_have_size.
    """

    def __init__(self, selector: Union[str, tuple, Locator], config: Optional[Configuration] = None,
                 context: Element | None = None, name: Optional[str] = None):
        self.locator = _resolve_selector(selector)
        self.config: Configuration = config or DriverManager.get_current_config()
        self.context = context
        self.name = name or str(self.locator)
        self.waiter = Waiter(
            timeout_s=max(0.001, self.config.wait_timeout_ms / 1000.0),
            poll_s=max(0.001, self.config.polling_interval_ms / 1000.0),
        )

    def _driver(self) -> WebDriver:
        return DriverManager.get_driver(self.config)

    def _resolve(self) -> List[WebElement]:
        if self.context:
            parent = self.context._resolve()
            return parent.find_elements(self.locator.by, self.locator.value)
        return self._driver().find_elements(self.locator.by, self.locator.value)

    def first(self) -> Element:
        return self.get(0)

    def get(self, index: int) -> Element:
        # child element resolved by index lazily
        # using XPath index to avoid stale when ref list changed (best-effort)
        if self.locator.by.lower() == "xpath":
            x = f"({self.locator.value})[{index + 1}]"
            return Element(("xpath", x),
                           config=self.config,
                           context=self.context,
                           name=f"{self.name}[{index}]")
        return IndexedElement(self, index, name=f"{self.name}[{index}]")

    def size(self) -> int:
        try:
            return len(self._resolve())
        except Exception:
            return 0

    def texts(self) -> List[str]:
        values: List[str] = []
        for el in self._resolve():
            try:
                values.append((el.text or "").strip())
            except StaleElementReferenceException:
                # Applying best-effort will ignore stale element
                continue
        return values

    def should_have_size(self, n: int, timeout_ms: Optional[int] = None) -> "Elements":
        orig_timeout = self.waiter.timeout_s
        if timeout_ms is not None:
            self.waiter.timeout_s = max(0.001, timeout_ms / 1000.0)

        def _supplier() -> bool:
            try:
                return len(self._resolve()) == n
            except (NoSuchElementException, StaleElementReferenceException):
                # If parent element not found, treat as 0 element
                return n == 0

        def _on_timeout() -> str:
            # Similar _supplier(), ensure there is no exception during get the length of element
            try:
                actual = len(self._resolve())
            except Exception:
                actual = 0

            return f'Elements("{self.name}") expected size={n}, actual={actual}. Locator={self.locator}'

        def _shot(path: str) -> bool:
            try:
                return self._driver().save_screenshot(path)
            except Exception:
                return False

        try:
            self.waiter.until(_supplier, _on_timeout, _shot)
            return self
        finally:
            self.waiter.timeout_s = orig_timeout


class IndexedElement(Element):
    """
    Proxy an element in the collection by index (re-find each time to avoid staleness).
    """

    def __init__(self, collection: Elements, index: int, name: Optional[str] = None):
        super().__init__(collection.locator, config=collection.config, context=collection.context, name=name)
        self._collection = collection
        self._index = index

    def _find_now(self) -> WebElement:
        els = self._collection._resolve()
        if self._index < 0 or self._index >= len(els):
            raise NoSuchElementException(
                f"Index {self._index} is out of range (size={len(els)}) for {self._collection.name}")
        return els[self._index]
