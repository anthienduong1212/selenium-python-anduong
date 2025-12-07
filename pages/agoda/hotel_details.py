import allure
from typing import Any, Dict, List

from core.element.conditions import visible as cond_visible, attribute_contains
from core.element.locator import Locator
from core.report.reporting import AllureReporter
from pages.agoda.enums.detailed_navbar_options import NavbarOptions
from pages.base_page import BasePage


class HotelDetails(BasePage):
    def __init__(self):
        super().__init__()

    # -------- NAVBAR ----------
    _NAV_NAVBAR = Locator.xpath("//div[@id='navbar']", "HOTEL_DETAILS Nav Bar")
    _BTN_NAVBAR_OPTION = Locator.xpath("//button[@aria-label={option} and not(@aria-hidden)]"
                                       , "HOTEL_DETAILS Nav Bar {option}")

    # -------- ROOM OPTIONS ---------
    _GRD_ROOM_FILTER = Locator.xpath("//div[contains(@id,'room-grid')]", "HOTEL_DETAILS Room Offer Filter")
    _OPT_ROOM_FILTER_OPTION = Locator.xpath("//div[@data-selenium='RoomGridFilter-filter']//div[normalize-space(.)={"
                                           "option}]", "HOTEL_DETAILS Room Offer Option {option}")

    # -------- FAVORITES -----------
    _BTN_ADD_TO_FAVORITES = Locator.xpath("//div[@data-element-name='hotel-mosaic']//button["
                                         "@data-selenium='favorite-heart']", "HOTEL_DETAILS Add to favorite")


    # -------- INFORMATION -----------
    _TXT_HOTEL_INFO_PARENT = Locator.xpath("//div[@id='property-main-content']")
    _TXT_HOTEL_NAME = Locator.xpath("//h1[@data-selenium='hotel-header-name']")
    _TXT_HOTEL_ADDRESS = Locator.xpath("//span[@data-selenium='hotel-address-map']")

    @allure.step("Select {option} on NavBar")
    def select_navbar_option(self, option: NavbarOptions):
        format_option_locator = self._BTN_NAVBAR_OPTION(option=option)
        nested_locator = self._NAV_NAVBAR.within(format_option_locator)
        option = self.el(nested_locator).should_be(cond_visible())
        option.click()

    @allure.step("Wait for Room Filter displays")
    def wait_for_room_filter_display(self) -> "Element":
        return self.el(self._GRD_ROOM_FILTER).should_be(cond_visible())

    @allure.step("Check the option display or not")
    def is_option_display(self, filter_name: str, filters: List[Dict[str, str]]):
        self.select_navbar_option(NavbarOptions.ROOMS)
        parent = self.wait_for_room_filter_display()
        result: list = []

        for filter_dict in filters:
            option = filter_dict.get(filter_name)
            if option is not None:
                try:
                    (parent.find(self._OPT_ROOM_FILTER_OPTION(option=option))
                                 .should_be(cond_visible()))
                except Exception:
                    with AllureReporter.step(f"Missing option: {option}"):
                        result.append({"option": option, "isDisplayed": False})
        return False if len(result) > 0 else True

    @allure.step("Add hotel to favorite")
    def add_to_favorites(self):
        fav_btn = self.el(self._BTN_ADD_TO_FAVORITES).should_be(cond_visible())
        fav_btn.scroll_into_view("wheel")
        if fav_btn.should_be(attribute_contains("aria-pressed", "false")):
            fav_btn.click()

    @allure.step("Wait for hotel information display")
    def wait_for_hotel_information_display(self) -> "Element":
        return self.el(self._TXT_HOTEL_INFO_PARENT).should_be(cond_visible())

    @allure.step("Get details of hotel information")
    def get_hotel_information(self) -> dict[str, Any]:
        parent = self.wait_for_hotel_information_display()
        parent.scroll_into_view("wheel")

        hotel_name = parent.find(self._TXT_HOTEL_NAME).text()
        hotel_addr = parent.find(self._TXT_HOTEL_ADDRESS).text()

        return {"name": hotel_name, "address": hotel_addr}

    @allure.step("Checking hotel information")
    def is_hotel_information_correct(self, expected: dict[str, Any]) -> bool:
        actual = self.get_hotel_information()
        different_values = {}
        common_keys = set(actual.keys()) & set(expected.keys())

        for key in common_keys:
            if actual[key] != expected[key]:
                with AllureReporter.step(f"Missing matching infor ACTUAL [{actual[key]}] | EXPECTED [{expected[key]}]"):
                    different_values[key] = {
                        'actual': actual[key],
                        'expected': expected[key]
                    }

        return False if len(different_values) > 0 else True
