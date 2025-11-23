from __future__ import annotations

import re
from typing import Callable, Iterable, Optional

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from core.configuration.configuration import Configuration
from core.driver.driver_conditions import (
    document_ready_state_complete,
    new_window_appeared,
    get_new_window_handle)
from core.driver.driver_manager import DriverManager
from core.driver.driver_wait import DriverWait
from core.report.reporting import AllureReporter
from core.waiter.wait import Waiter


class BrowserUtils:
    @staticmethod
    def _driver():
        return DriverManager.get_current_driver()

    @staticmethod
    def _cfg() -> Configuration:
        return DriverManager.get_current_config()

    @staticmethod
    def _waiter() -> Waiter:
        cfg = BrowserUtils._cfg()
        return Waiter(timeout_s=cfg.wait_timeout_ms / 1000.0,
                      poll_s=cfg.polling_interval_ms / 1000.0)

    # ----------------------------
    #      TAB_SWITCHING_WAIT
    # ----------------------------

    @staticmethod
    def wait_ready_state_complete():
        """
        Wait document.readyState == 'complete' at current tab.
        """
        d = BrowserUtils._driver()
        desc = "Wait for document ready state is 'complete'"
        with AllureReporter.step(desc):
            BrowserUtils._waiter().until(
                supplier=lambda: document_ready_state_complete(d),
                on_timeout=lambda: f"{desc}. url={getattr(d,'current_url',None)} title={getattr(d,'title',None)}"
            )

    @staticmethod
    def wait_for_window_count(count: int, timeout_s: Optional[float] = None):
        """
        Wait for the number of windows/tabs to equal 'count'.
        """
        d = BrowserUtils._driver()
        cfg = BrowserUtils._cfg()
        to = timeout_s if timeout_s is not None else (cfg.wait_timeout_ms / 1000.0)
        po = cfg.polling_interval_ms / 1000.0
        with AllureReporter.step(f"Wait for window count({count})"):
            WebDriverWait(d, to, po).until(EC.number_of_windows_to_be(count))

    @staticmethod
    def wait_for_new_window(old_handles: Iterable[str]) -> str:
        """
        Wait for a new handle to appear compared to the old list and return the new handle.
        """
        d = BrowserUtils._driver()
        desc = "New window is opened"
        with AllureReporter.step(desc):
            BrowserUtils._waiter().until(
                supplier=lambda: new_window_appeared(d, old_handles),
                on_timeout=lambda: f"{desc}. current_handles={d.window_handles}"
            )
        new_handle = get_new_window_handle(d, old_handles)
        if new_handle is None:
            raise RuntimeError("Wait succeeded but new handle not found.")
        return new_handle

    # ----------------------------
    #      TAB_SWITCHING_ACTION
    # ----------------------------

    @staticmethod
    def switch_to(handle: str) -> None:
        with AllureReporter.step(f"Switch back to({handle})"):
            BrowserUtils._driver().switch_to.window(handle)

    @staticmethod
    def force_same_tab_link() -> None:
        """
        Call BEFORE click to have target=_blank / window.open links open in the current tab.
        Do not use if you are testing multi-tab behavior.
        """
        d = BrowserUtils._driver()
        with AllureReporter.step("Force to same tab links"):
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



