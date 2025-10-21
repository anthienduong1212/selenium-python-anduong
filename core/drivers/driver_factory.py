from __future__ import annotations
from typing import Optional, Type
from selenium.webdriver.remote.webdriver import WebDriver
from core.configs.config import Configuration
from core.providers.browser_provider import BrowserProvider
from core.providers.registry import discover_and_register, get_provider_class


class DriverFactory:
    """
    A simple factory means to create WebDriver by Browser Name
    Detailed configuration (headless, remote_url, args, prefs, capabilities…) will be stored on
    `Configuration` and handle by itself. DriverManager will use this class when they need to create a new driver.
    """

    def __init__(self, provider_package: str = "core.providers"):
        discover_and_register(provider_package)


    def create_driver(self, config: Configuration) -> WebDriver:
        """
        Create driver based on configuration.
        :param config: Configuration object with preset browser (chrome, firefox, edge…),
                        headless, remote_url… Providers will read extra args/prefs/caps from config.
        :return: WebDriver instance.
        """
        browser_name = (config.browser or "").lower()
        provider_cls: Optional[Type[BrowserProvider]] = get_provider_class(browser_name)
        if not provider_cls:
            raise ValueError(f"Browser '{browser_name}' is not supported or provider not registered.")

        provider = provider_cls(config=config)
        return provider.create_driver()
