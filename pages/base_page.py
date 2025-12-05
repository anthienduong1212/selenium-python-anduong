from __future__ import annotations

import allure

from core.configuration.configuration import Configuration
from core.driver.driver_manager import DriverManager
from core.element.element import Element, Elements
from core.logging.logging import Logger


class BasePage:
    """
    Base class for Page Object. Each Page inherits this class for easy element access.
    Use Element / Elements with current config.
    """

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


