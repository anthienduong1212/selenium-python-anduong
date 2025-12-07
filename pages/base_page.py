from __future__ import annotations

import allure

from core.driver.driver_manager import DriverManager
from core.element.locator import Locator
from core.element.element import Element, Elements
from core.logging.logging import Logger


class BasePage:
    """
    Base class for Page Object. Each Page inherits this class for easy element access.
    Use Element / Elements with current config.
    """
    _BTN_LOGIN = Locator.xpath("//div[@data-testid='responsive-action-bar']//button[@data-element-name='sign-in-button']",
                               "LOGIN_PAGE Login button")

    def __init__(self):
        self.driver = DriverManager.get_current_driver()
        if self.driver is None:
            Logger.error("Driver is not initialized or available in context.")

    def el(self, selector):
        return Element(selector)

    def els(self, selector):
        return Elements(selector)

    @allure.step("Navigate to {url}")
    def open(self, url: str):
        self.driver.get(url)

    @allure.step("Click login button")
    def click_login(self):
        el = self.el(self._BTN_LOGIN)
        el.scroll_into_view("wheel")
        el.click()
