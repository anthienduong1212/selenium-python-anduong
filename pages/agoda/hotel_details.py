from pages.base_page import BasePage
from core.element.locators import Locator
from selenium.webdriver.common.by import By
from core.configs.config import Configuration
from core.utils.browser_utils import BrowserUtils
from core.element.conditions import Condition, visible as cond_visible
from core.utils.datetime_utils import get_current_date, parse_strict

class HotelDetails(BasePage):
    def __init__(self, config: Configuration):
        super().__init__()
        self.config = config

