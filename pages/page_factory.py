from __future__ import annotations
from typing import Type, TypeVar
from core.configs.config import Configuration


class PageFactory:
    """
    Create Page Object with same configuration (browser, timeout, ...).
    Helps reuse configuration between pages without having to manually transfer.
    """

    def __init__(self, config: Configuration | None = None):
        self.config = config or Configuration()

    def create(self, page_cls: Type[T]) -> T:
        """
        Instantiate a Page (class inherits BasePage) and pass config to it.
        :param page_cls: page class to instantiate
        :return: instance of page with assigned config
        """
        return page_cls(self.config)
