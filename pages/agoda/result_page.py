from __future__ import annotations
from pages.base_page import BasePage
from core.element.locators import Locator
from selenium.webdriver.common.by import By
from core.utils.browser_utils import BrowserUtils
from core.utils.string_utils import contains_text
from core.element.conditions import Condition, visible as cond_visible
from core.utils.datetime_utils import parse_strict
from typing import Tuple


class ResultPage(BasePage):

    def __init__(self):
        super().__init__()

    # -------- HOTEL RESULT CARDS ------------
    LI_HOTEL_INFORMATION = Locator.xpath("//li[@data-selenium='hotel-item']", "RESULT_PAGE Hotel Result Information")
    LBL_HOTEL_INFORMATION_NAME = Locator.xpath("//h3[@data-selenium='hotel-name']", "RESULT_PAGE Hotel Name")
    LBL_HOTEL_ADDRESS = Locator.xpath("//button[@data-selenium='area-city-text']//span", "RESULT_PAGE Hotel City")
    LBL_HOTEL_ROOM_OFFER = Locator.xpath("//div[@data-element-name='pill-each-item']/span[contains(text(),"
                                         "{offer_name})]", "RESULT_PAGE Room offer {offer_name}")

    # -------------- FILTER ----------------
    LBL_FILTER = Locator.xpath("//legend[contains(@id,{filter_name})]/following-sibling::ul",
                               "RESULT_PAGE Room Offer Filter {filter_name}")
    OPT_FILTER_OPTION = Locator.xpath("//div[.//span[normalize-space(.)={option_name}]]/preceding-sibling::div//input"
                                      ,"RESULT_PAGE Filter option {option_name}")

    def get_top_n_hotels(self, n: int, city: str) -> list[Dict[str, Any]]:
        """
        Verify: Top n LI_HOTEL_INFORMATION elements have:
        - name exists & not empty
        - address contains 'city' (tolerant of accents/case-sensitive/spaces)

        Raise AssertionError with details if any card fails.
        """

        cards = self.els(self.LI_HOTEL_INFORMATION)
        hotel_data_list = []

        for i in range(n):
            card = cards.get(i)
            name_el = card.find(self.LBL_HOTEL_INFORMATION_NAME)
            addr_el = card.find(self.LBL_HOTEL_ADDRESS)

            name = (name_el.text() or "").strip()
            addr = (addr_el.text() or "").strip()

            hotel_data_list.append({"name": name, "address": addr})

            if not name:
                empty_names.append(i)
            if not contains_text(addr, city):
                mismatches.append((i, addr))

        return list(hotel_data_list)

    def get_missing_data(self, hotel_data: Tuple[Dict[str, Any], ...], city: str) -> Tuple[List[int], List[Tuple[int, str]]]:
        mismatched_cities: List[Tuple[int, str]] = []
        empty_names: List[int] = []

        for i, data in enumerate(hotel_data):
            if not data.get("name"):
                empty_names.append(i)
            if not contains_text(data.get("address"), city):
                mismatched_cities.append(i)

        return empty_names, mismatched_cities

    def search_filter_with_term(self, filter_name: str, option_name: str):
        """
        Select an option on filter base on filter_name
        :param filter_name: Name of filter
        :param option_name: Name of option
        """
        parent = self.el(self.LBL_FILTER(filter_name=filter_name)).should_be(cond_visible())
        child = parent.find(self.OPT_FILTER_OPTION(option_name=option_name))
        child.click()

    def select_first_hotel(self):
        hotel = self.els(self.LI_HOTEL_INFORMATION).get(0)
        BrowserUtils.force_same_tab_link()
        hotel.click()
