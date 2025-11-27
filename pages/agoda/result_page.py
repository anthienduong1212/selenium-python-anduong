from __future__ import annotations

import allure
from typing import Tuple, List, Dict

from selenium.webdriver.common.by import By

from core.element.conditions import Condition
from core.element.conditions import visible as cond_visible
from core.element.locator import Locator
from core.utils.browser_utils import BrowserUtils
from core.utils.datetime_utils import parse_strict
from core.logging.logging import Logger
from core.utils.string_utils import contains_text
from pages.base_page import BasePage


class ResultPage(BasePage):

    def __init__(self):
        super().__init__()

    # -------- HOTEL RESULT CARDS ------------
    LI_HOTEL_INFORMATION = Locator.xpath("//li[@data-selenium='hotel-item']", "RESULT_PAGE Hotel Result Information")
    LBL_HOTEL_INFORMATION_NAME = Locator.xpath("//h3[@data-selenium='hotel-name']", "RESULT_PAGE Hotel Name")
    LBL_HOTEL_ADDRESS = Locator.xpath("//button[@data-selenium='area-city-text']//span", "RESULT_PAGE Hotel City")
    LBL_HOTEL_ROOM_OFFER = Locator.xpath("//div[@data-element-name='pill-each-item']/span[contains(text(),"
                                         "{offer_name})]", "RESULT_PAGE Room offer")

    # -------------- FILTER ----------------
    LBL_FILTER = Locator.xpath("//legend[contains(@id,{filter_name})]/following-sibling::ul",
                               "RESULT_PAGE Room Offer Filter")
    OPT_FILTER_OPTION = Locator.xpath("//div[.//span[normalize-space(.)={option_name}]]/preceding-sibling::div//input"
                                      , "RESULT_PAGE Filter option")

    @allure.step("Get information of first {n} hotels in {city}")
    def get_search_hotel_results(self, n: int, city: str) -> list[Dict[str, Any]]:
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

    @allure.step("Checking hotel which is missing data")
    def checking_hotel_address_from_search(self, n: int, city: str) -> List[Tuple[int, str]]:
        """
        Get the list of data and extract which data fields is missing
        :param n: Number of result
        :param city: matching term
        :return: List of hotel which is missing their information
        """
        hotel_data = self.get_search_hotel_results(n, city)

        mismatched_cities: List[Tuple[int, str]] = []

        for i, data in enumerate(hotel_data):
            if not contains_text(data.get("address"), city):
                mismatched_cities.append(i)

        return False if len(mismatched_cities) > 0 else True

    @allure.step("Filter {filter_name} with available option")
    def filter_with_term(self, filter_name: str, filters: List[Dict[str, str]]):
        """
        Select an option on filter base on filter_name
        :param filter_name: Name of filter
        :param filters: List of filter with it option
        """
        found_filter = [d for d in filters if filter_name in d]
        if found_filter:
            option = found_filter[filter_name]
            parent = self.el(self.LBL_FILTER(filter_name=filter_name)).should_be(cond_visible())
            child = parent.find(self.OPT_FILTER_OPTION(option_name=option))
            child.scroll_into_view()
            child.click()
        else:
            Logger.error(f"Filter {filter_name} not found")

    @allure.step("Select the first hotel on result")
    def select_first_hotel(self):
        """Select first hotel in search result"""
        hotel = self.els(self.LI_HOTEL_INFORMATION).get(0)
        BrowserUtils.force_same_tab_link()
        hotel.click()
