from typing import Tuple, Dict, Any
from pages.base_page import BasePage
from core.element.locators import Locator
from core.utils.browser_utils import BrowserUtils
from pages.agoda.enums.detailed_navbar_options import NavbarOptions
from core.element.conditions import Condition, visible as cond_visible


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

    def select_navbar_option(self, option: NavbarOptions):
        format_option_locator = self.BTN_NAVBAR_OPTION(option=option)

        # Apply this because the parent locator is duplicated but distinct by its child element
        nested_locator = self.NAV_NAVBAR.within(format_option_locator)
        option = self.el(nested_locator).should_be(cond_visible())
        option.click()

    def is_option_display(self, option: str):
        room_filter = self.el(self.GRD_ROOM_FILTER).should_be(cond_visible())
        option = room_filter.find(self.OPT_ROOM_FILTER_OPTION(option=option))

        return option.exists()

    def add_to_favorites(self):
        self.el(self.BTN_ADD_TO_FAVORITES).should(cond_visible()).click()

    def get_hotel_information(self) -> dict[str, Any]:
        parent = self.el(self.TXT_HOTEL_INFO_PARENT).should_be(cond_visible())
        parent.scroll_into_view()

        hotel_name = parent.find(self.TXT_HOTEL_NAME).text()
        hotel_addr = parent.find(self.TXT_HOTEL_ADDRESS).text()

        return {"name": hotel_name, "address": hotel_addr}
