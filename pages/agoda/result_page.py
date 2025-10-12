from pages.base_page import BasePage
from core.element.locators import Locator
from selenium.webdriver.common.by import By
from core.configs.config import Configuration
from core.utils.string_utils import contains_text
from core.element.conditions import Condition, visible as cond_visible
from core.utils.datetime_utils import get_current_date, parse_strict


class ResultPage(BasePage):

    def __init__(self, config: Configuration):
        super().__init__()
        self.config = config

    LI_HOTEL_INFORMATION = Locator.xpath("//li[@data-selenium='hotel-item']", "Hotel Result Information")
    LBL_HOTEL_INFORMATION_NAME = Locator.xpath("//h3[@data-selenium='hotel-name']", "Hotel Name")
    LBL_HOTEL_ADDRESS = Locator.xpath("//button[@data-selenium='area-city-text']//span", "Hotel City")

    def verify_top_n_hotels_are_in_city(self, n: int, city: str):
        """
        Verify: Top n LI_HOTEL_INFORMATION elements have:
        - name exists & not empty
        - address contains 'city' (tolerant of accents/case-sensitive/spaces)

        Raise AssertionError with details if any card fails.
        """

        cards = self.els(self.LI_HOTEL_INFORMATION)

        mismatches: List[Tuple[int, str]] = []
        empty_names: List[int] = []

        for i in range(n):
            card = cards.get(i)
            name_el = card.find(self.LBL_HOTEL_INFORMATION_NAME)
            addr_el = card.find(self.LBL_HOTEL_ADDRESS)

            name = (name_el.text() or "").strip()
            addr = (addr_el.text() or "").strip()

            if not name:
                empty_names.append(i)
            if not contains_text(addr, city):
                mismatches.append((i, addr))

        assert not empty_names, f"Missing name hotel at index: {empty_names}"
        assert not mismatches, f"Hotel with mismatched city '{city}' at: {mismatches}"
    
