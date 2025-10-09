from __future__ import annotations
from typing import Optional, List, Union
from dataclasses import replace
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.common.exceptions import JavascriptException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from core.element.locators import Locator
from core.waiter.wait import Waiter
from core.element.conditions import Condition, visible as cond_visible
from core.reports.reporting import step, attach_text, attach_png

try:
    import allure
except Exception:
    import contextlib


    class _NoAllure:
        def step(self, *_a, **_k): return contextlib.nullcontext()

        def attach(self, *_a, **_k): pass


    allure = _NoAllure()

from core.drivers.driver_manager import DriverManager
from core.configs.config import Configuration


# --------- helper ---------------------
def _resolve_selector(selector: Union[str, tuple, Locator]) -> Locator:
    return Locator.from_any(selector)


class Element:
    """
   Selenide-like Element:
     - lazy locating (chỉ find khi cần)
     - auto-wait với .should(...)
     - fluent API: .click().type("...").should(be_visible())
     - context-find: parent.find("child")
   """

    def __init__(self, selector, config=None, context=None, name=None):
        self.locator: Locator = _resolve_selector(selector)
        self.config = config or Configuration()
        self.context = context
        self.name = name or str(self.locator)
        self._last_ref: Optional[WebElement] = None

        self.waiter = Waiter(timeout_s=self.config.wait_timeout_ms / 1000.0,
                             poll_s=self.config.polling_interval_ms / 1000.0, )

    def _driver(self) -> WebDriver:
        return DriverManager.get_driver(self.config)

    def _find_now(self) -> WebElement:
        loc = self.locator
        # If Element has context but locator doesn't have parent -> graft parent from context
        if getattr(self, "context", None) and not getattr(loc, "parent", None):
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

        if getattr(self.config, "auto_scroll", True):
            self.scroll_into_view()
        return self._last_ref

    def find(self, selector: Union[str, tuple, Locator], name: Optional[str] = None) -> "Element":
        return Element(selector, config=self.config, context=self, name=name)

    def all(self, selector: Union[str, tuple, Locator], name: Optional[str] = None) -> "Elements":
        return Elements(selector, config=self.config, context=self, name=name)

    # ---------- core / action ---------------
    def click(self) -> "Element":
        self.should(cond_visible())
        self._resolve().click()
        return self

    def type(self, text: str, clear: bool = True) -> "Element":
        self.should(cond_visible())
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
        ActionChains(self._driver()).move_to_element(self._resolve()).perform()
        return self

    def is_in_viewport(self) -> bool:
        return self._driver().execute_script("""
        const r = arguments[0].getBoundingClientRect();
        const vh = window.innerHeight || document.documentElement.clientHeight;
        const vw = window.innerWidth  || document.documentElement.clientWidth;
        return r.top >= 0 && r.left >= 0 && r.bottom <= vh && r.right <= vw;
    """, self._resolve())

    def scroll_js(self):
        self._driver().execute_script("""
        const el = arguments[0], block = arguments[1], offset = arguments[2]||0;
        el.scrollIntoView({block: block, inline: 'nearest'});
        if (offset) window.scrollBy(0, -offset);
    """, self._resolve(), self.config.scroll_block, self.config.header_offset_px)

    def scroll_wheel(self):
        ActionChains(self._driver()).scroll_to_element(self._resolve()).perform()

    def scroll_move(self):
        ActionChains(self._driver()).move_to_element(self._resolve()).perform()

    def scroll_into_view(self):
        try:
            if self.is_in_viewport():
                return
        except JavascriptException:
            pass

        backend = self.config.scroll_backend

        try:
            if backend == "js":
                self.scroll_js()
            elif backend == "wheel":
                self.scroll_wheel()
            elif backend == "move":
                self.scroll_move()
            else:
                self.scroll_js()
        except Exception:
            self.scroll_move()

        import time
        t0 = time.time()
        last_top = None
        while time.time() < t0 - 0.5:
            top = self._driver().execute_script("return arguments[0].getBoundingClientRect().top;", self._resolve())
            if last_top is not None and abs(top - last_top) < 0.5:
                break
            last_top = top
            time.sleep(0.05)

        if not self.is_in_viewport() and self.config.header_offset_px:
            self._driver().execute_script("window.scrollBy(0, -arguments[0]);", self.config.header_offset_px)

    def resolve_we(self, locator) -> WebElement:
        """
        Context-aware resolve:
        - If locator has parent -> resolve parent and find in CONTEXT parent
        - If not -> find from driver
        """
        if self.parent:
            parent_we = self.resolve_we(locator)
            return parent_we.find_element(locator.by, locator.value)
        return self._driver().find_element(locator.by, locator.value)

    # ---------- state getters ----------
    def text(self, mode: sttr = "visible") -> str:
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
                return (el.get_attribute("textContext") or "").strip()
            elif mode == "value":
                return (el.get_property("value") or el.get_attribute("value") or "").strip()
            else:
                # Default value same as VISIBLE
                return (el.text or el.get_attribute("innerText") or "").strip()
        except Exception:
            return ""

    def attr(self, name: str) -> Optional[str]:
        return self._resolve().get_attribute(name)

    def css(self, name: str) -> Optional[str]:
        return self._resolve().value_of_css_property(name)

    # ---------- waiting / assertions ----------

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

            # Verify all conditions on found element
            return all(c.test(el) for c in conditions)

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

        with step(desc):
            try:
                self.waiter.until(_supplier, _on_timeout, _shot)
                return self
            except Exception as e:
                # Attach information about failure (screenshot, locator)
                spath = getattr(e, "screenshot_path", None)
                if spath:
                    attach_png(f"FAILED - {self.name}", spath)
                attach_text("Locator", str(self.locator))
                raise
            finally:
                self.waiter.timeout_s = orig_timeout

    def should_be(self, *conditions: Condition, timeout_ms: Optional[int] = None) -> "Element":
        return self.should(*conditions, timeout_ms=timeout_ms)

    def should_have(self, *conditions: Condition, timeout_ms: Optional[int] = None) -> "Element":
        return self.should(*conditions, timeout_ms=timeout_ms)

    # ------------ with ---------------
    def _with(self, **overrides) -> "Element":
        """
            Create a copy of Element with config override
        """
        new_cfg = self.config
        for k, v in overrides.items():
            if hasattr(new_cfg, k):
                setattr(new_cfg, k, v)
        return Element(self.locator, config=new_cfg, context=self.context, name=self.name)

    def as_(self, name: str) -> "Element":
        return Element(self.locator.with_decs(name), config=self.config, context=self.context, name=name)

    def exists(self) -> bool:
        try:
            self._resolve()
            return True
        except NoSuchElementException:
            return False
        except StaleElementReferenceException:
            return False


class Elements:
    """
    Element Collection.
    Lazy: find_elements needed, support filter/map/first/get/size + should_have_size.
    """

    def __init__(self, selector: Union[str, tuple, Locator], config: Optional[Configuration] = None,
                 context: Element | None = None, name: Optional[str] = None):
        self.locator = _resolve_selector(selector)
        self.config = config or Configuration()
        self.context = context
        self.name = name or str(self.locator)

        self.waiter = Waiter(
            timeout_s=self.config.wait_timeout_ms / 1000.0,
            poll_s=self.config.polling_interval_ms / 1000.0,
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
            x = f"{self.locator.value}[{index + 1}]"
            return Element(("xpath", x),
                           config=self.config,
                           context=self.context,
                           name=f"{self.name}[{index}]")

        return IndexedElement(self, index, name=f"{self.name}[{index}]")

    def size(self) -> int:
        return len(self._resolve())

    def texts(self) -> List[str]:
        return [el.text or "" for el in self._resolve()]

    def should_have_size(self, n: int, timeout_ms: Optional[int] = None) -> "Elements":
        orig_timeout = self.waiter.timeout_s
        if timeout_ms is not None:
            self.waiter.timeout_s = max(0.001, timeout_ms / 1000.0)

        def _supplier() -> bool:
            try:
                current_count = len(self._resolve())
            except (NoSuchElementException, StaleElementReferenceException):
                # If parent element not found, treat as 0 element
                current_count = 0

            return current_count == n

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
    Proxy một phần tử trong collection bằng index (tìm lại mỗi lần để tránh stale).
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
