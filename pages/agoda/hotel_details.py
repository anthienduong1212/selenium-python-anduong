import allure
from typing import Any, Dict, Tuple

from core.element.conditions import Condition
from core.element.conditions import visible as cond_visible
from core.element.locator import Locator
from core.utils.browser_utils import BrowserUtils
from pages.agoda.enums.detailed_navbar_options import NavbarOptions
from pages.base_page import BasePage


class HotelDetails(BasePage):
    def __init__(self):
        super().__init__()

    # -------- NAVBAR ----------
    NAV_NAVBAR = Locator.xpath("//div[@id='navbar']", "HOTEL_DETAILS Nav Bar")
    BTN_NAVBAR_OPTION = Locator.xpath("//button[@aria-label={option} and not(@aria-hidden)]"
                                      , "HOTEL_DETAILS Nav Bar {option}")

    # -------- ROOM OPTIONS ---------
    GRD_ROOM_FILTER = Locator.xpath("//div[contains(@id,'room-grid')]", "HOTEL_DETAILS Room Offer Filter")
    OPT_ROOM_FILTER_OPTION = Locator.xpath("//div[@data-selenium='RoomGridFilter-filter']//div[normalize-space(.)={"
                                           "option}]", "HOTEL_DETAILS Room Offer Option {option}")

    # -------- FAVORITES -----------
    BTN_ADD_TO_FAVORITES = Locator.xpath("//div[@data-element-name='hotel-mosaic']//button["
                                         "@data-selenium='favorite-heart']", "HOTEL_DETAILS Add to favorite")

    # -------- INFORMATION -----------
    TXT_HOTEL_INFO_PARENT = Locator.xpath("//div[@id='property-main-content']")
    TXT_HOTEL_NAME = Locator.xpath("//h1[@data-selenium='hotel-header-name']")
    TXT_HOTEL_ADDRESS = Locator.xpath("//span[@data-selenium='hotel-address-map']")

    @allure.step("Select {option} on NavBar")
    def select_navbar_option(self, option: NavbarOptions):
        format_option_locator = self.BTN_NAVBAR_OPTION(option=option)
        nested_locator = self.NAV_NAVBAR.within(format_option_locator)
        option = self.el(nested_locator).should_be(cond_visible())
        option.click()

    @allure.step("Wait for Room Filter displays")
    def wait_for_room_filter_display(self) -> "Element":
        return self.el(self.GRD_ROOM_FILTER).should_be(cond_visible())

    @allure.step("Check the {option} display or not")
    def is_option_display(self, option: str):
        self.select_navbar_option(NavbarOptions.ROOMS)
        parent = self.wait_for_room_filter_display()

        option = parent.find(self.OPT_ROOM_FILTER_OPTION(option=option))
        return option.exists()

    @allure.step("Add hotel to favorite")
    def add_to_favorites(self):
        fav_btn = self.el(self.BTN_ADD_TO_FAVORITES)
        fav_btn.scroll_into_view("wheel")
        fav_btn.click()

    @allure.step("Wait for hotel information display")
    def wait_for_hotel_information_display(self) -> "Element":
        return self.el(self.TXT_HOTEL_INFO_PARENT).should_be(cond_visible())

    @allure.step("Get details of hotel information")
    def get_hotel_information(self) -> dict[str, Any]:
        parent = self.wait_for_hotel_information_display()
        parent.scroll_into_view("wheel")

        hotel_name = parent.find(self.TXT_HOTEL_NAME).text()
        hotel_addr = parent.find(self.TXT_HOTEL_ADDRESS).text()

        return {"name": hotel_name, "address": hotel_addr}
