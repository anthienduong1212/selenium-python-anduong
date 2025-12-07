from __future__ import annotations

import allure
from typing import Tuple, List, Dict, Any

from core.element.conditions import visible as cond_visible
from core.element.locator import Locator
from core.report.reporting import AllureReporter
from core.utils.browser_utils import BrowserUtils
from core.logging.logging import Logger
from core.utils.string_utils import contains_text
from pages.base_page import BasePage


class ResultPage(BasePage):

    def __init__(self):
        super().__init__()

    # -------- HOTEL RESULT CARDS ------------
    _LI_HOTEL_INFORMATION = Locator.xpath("//li[@data-selenium='hotel-item']", "RESULT_PAGE Hotel Result Information")
    _LBL_HOTEL_INFORMATION_NAME = Locator.xpath("//h3[@data-selenium='hotel-name']", "RESULT_PAGE Hotel Name")
    _LBL_HOTEL_ADDRESS = Locator.xpath("//button[@data-selenium='area-city-text']//span", "RESULT_PAGE Hotel City")
    _LBL_HOTEL_ROOM_OFFER = Locator.xpath("//div[@data-element-name='pill-each-item']/span[contains(text(),"
                                          "{offer_name})]", "RESULT_PAGE Room offer")

    # -------------- FILTER ----------------
    _LBL_FILTER = Locator.xpath("//legend[contains(@id,{filter_name})]/following-sibling::ul",
                                "RESULT_PAGE Room Offer Filter")
    _OPT_FILTER_OPTION = Locator.xpath("//div[.//span[normalize-space(.)={option_name}]]/preceding-sibling::div//input"
                                       , "RESULT_PAGE Filter option")

    @allure.step("Get information of first {n} hotels")
    def get_search_hotel_results(self, n: int) -> list[Dict[str, Any]]:
        """
        Verify: Top n LI_HOTEL_INFORMATION elements have:
        - name exists & not empty
        - address contains 'city' (tolerant of accents/case-sensitive/spaces)

        Raise AssertionError with details if any card fails.
        """
        names = lambda: self.els(self._LI_HOTEL_INFORMATION.within(self._LBL_HOTEL_INFORMATION_NAME))
        addresses = lambda: self.els(self._LI_HOTEL_INFORMATION.within(self._LBL_HOTEL_ADDRESS))
        hotel_data_list = []

        for i in range(n):
            current_el: int = names().size()

            while current_el < n:
                BrowserUtils.scroll_by_half_page()
                current_el = names().size()

            names().get(i).scroll_into_view("wheel")
            name_el = names().get(i).text()
            addr_el = addresses().get(i).text()

            name = (name_el or "").strip()
            addr = (addr_el or "").strip()

            with AllureReporter.step(f"Adding hotel {name} has address {addr} to list"):
                hotel_data_list.append({"name": name, "address": addr})

        return list(hotel_data_list)

    @allure.step("Checking address of {n} hotels in {city}")
    def checking_hotel_address_from_search(self, n: int, city: str) -> List[Tuple[int, str]]:
        """
        Get the list of data and extract which data fields is missing
        :param n: Number of result
        :param city: matching term
        :return: List of hotel which is missing their information
        """
        hotel_data = self.get_search_hotel_results(n)

        mismatched_cities: List[Tuple[int, str]] = []

        for i, data in enumerate(hotel_data):
            if not contains_text(data.get("address"), city):
                name = data.get("name")
                with AllureReporter.step(f"Found hotel has missing address : {name}"):
                    mismatched_cities.append((i, name))

        return mismatched_cities

    @allure.step("Filter {filter_name} with available option")
    def filter_with_term(self, filter_name: str, filters: List[Dict[str, str]]):
        """
        Select an option on filter base on filter_name
        :param filter_name: Name of filter
        :param filters: List of filter with it option
        """
        for filter_dict in filters:
            if filter_name in filter_dict:
                option = filter_dict[filter_name]

                parent = self.el(self._LBL_FILTER(filter_name=filter_name)).should_be(cond_visible())
                child = parent.find(self._OPT_FILTER_OPTION(option_name=option))
                child.scroll_into_view("wheel")
                child.click()
            else:
                Logger.error(f"Filter {filter_name} not found")
                raise ValueError("Filter not found")

    @allure.step("Select the first hotel on result")
    def select_first_hotel(self):
        """Select first hotel in search result"""
        hotels = self.els(self._LI_HOTEL_INFORMATION)
        hotel = hotels.get(0).should_be(cond_visible())
        BrowserUtils.force_same_tab_link()
        hotel.click()
