from __future__ import annotations
from typing import Iterable, Callable, Optional
import re

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.configuration.configuration import Configuration
from core.driver.driver_manager import DriverManager
from core.driver.driver_conditions import DriverCondition
from core.waiter.wait import Waiter
from core.report.reporting import AllureReporter
from core.driver.driver_wait import DriverWait


class BrowserUtils:
    @staticmethod
    def _driver():
        return DriverManager.get_current_driver()

    @staticmethod
    def _cfg() -> Configuration:
        return DriverManager.get_current_config()

    @staticmethod
    def _dw() -> DriverWait:
        cfg = BrowserUtils._cfg()
        return DriverWait(cfg)

    @staticmethod
    def _explicit_wait(timeout_s: Optional[float] = None,
                       poll_s: Optional[float] = None) -> WebDriverWait:
        cfg = BrowserUtils._cfg()
        to = timeout_s if timeout_s is not None else (cfg.wait_timeout_ms / 1000.0)
        po = poll_s if poll_s is not None else (cfg.polling_interval_ms / 1000.0)
        return WebDriverWait(BrowserUtils._driver(), to, poll_frequency=po)

    # ----------------------------
    #      TAB_SWITCHING_WAIT
    # ----------------------------

    @staticmethod
    def wait_ready_state_complete():
        """
        Wait document.readyState == 'complete' at current tab.
        """
        d = BrowserUtils._driver()
        desc = "document.readyState == 'complete'"
        with AllureReporter.step(desc):
            BrowserUtils._dw().waiter.until(
                supplier=lambda: d.execute_script("return document.readyState") == "complete",
                on_timeout=lambda: f"{desc}. url={getattr(d,'current_url',None)} title={getattr(d,'title',None)}",
                take_screenshot=lambda p: d.save_screenshot(p),
            )

    @staticmethod
    def wait_for_window_count(count: int, timeout_s: Optional[float] = None):
        """
        Wait for the number of windows/tabs to equal 'count'.
        """
        with AllureReporter.step(f"wait_for_window_count({count})"):
            BrowserUtils._explicit_wait(timeout_s).until(EC.number_of_windows_to_be(count))

    @staticmethod
    def wait_for_new_window(old_handles: Iterable[str]) -> str:
        """
        Wait for a new handle to appear compared to the old list and return the new handle.
        """
        d = BrowserUtils._driver()
        old = set(old_handles)
        desc = "new_window_is_opened"
        with AllureReporter.step(desc):
            BrowserUtils._dw().waiter.until(
                supplier=lambda: len(set(d.window_handles) - old) >= 1,
                on_timeout=lambda: f"{desc}. current_handles={d.window_handles}",
                take_screenshot=lambda p: d.save_screenshot(p),
            )
        return list(set(d.window_handles) - old)[0]

    # ----------------------------
    #      TAB_SWITCHING_ACTION
    # ----------------------------

    @staticmethod
    def switch_to(handle: str) -> None:
        with AllureReporter.step(f"switch_back_to({handle})"):
            BrowserUtils._driver().switch_to.window(handle)

    @staticmethod
    def force_same_tab_link() -> None:
        """
        Call BEFORE click to have target=_blank / window.open links open in the current tab.
        Do not use if you are testing multi-tab behavior.
        """
        d = BrowserUtils._driver()
        with AllureReporter.step("force_same_tab_links()"):
            js = """
            document.querySelectorAll('a[target="_blank"]').forEach(a => a.removeAttribute('target'));
            window.open = function(url, name, specs){ window.location.href = url; return window; };
            """
            d.execute_script(js)

    @staticmethod
    def click_open_and_switch(click_action: callable):
        d = DriverManager.get_current_driver()
        before = d.window_handles[:]
        click_action()

        new_h = BrowserUtils.wait_for_new_window(before)
        BrowserUtils.switch_to(new_h)

        BrowserUtils.wait_ready_state_complete()

        return new_h



