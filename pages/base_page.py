from __future__ import annotations
from core.element.elements import Element, Elements
from core.configs.config import Configuration
from core.drivers.driver_manager import DriverManager


class BasePage:
    """
    Base class for Page Object. Each Page inherits this class for easy element access.
    Use Element / Elements with current config.
    """

    def __init__(self, config: Configuration | None = None):
        self.config = config or Configuration()
        self.driver = DriverManager.get_driver(self.config)

    def el(self, selector, name: str | None = None):
        return Element(selector, config=self.config, name=name)

    def els(self, selector, name: str| None = None):
        return Elements(selector, config=self.config, name=name)

    def open(self, url: str):
        self.driver.get(url)

