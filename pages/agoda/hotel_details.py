from pages.base_page import BasePage
from core.element.locators import Locator
from core.utils.browser_utils import BrowserUtils
from pages.agoda.enums.detailed_navbar_options import NavbarOptions

from core.element.conditions import Condition, visible as cond_visible
from core.utils.datetime_utils import get_current_date, parse_strict


class HotelDetails(BasePage):
    def __init__(self):
        super().__init__()

    # -------- NAVBAR ----------
    NAV_NAVBAR = Locator.xpath("//div[@id='navbar']")
    BTN_NAVBAR_OPTION = Locator.xpath("//button[@aria-label={option} and not(@aria-hidden)]")

    # -------- ROOM OPTIONS ---------
    GRD_ROOM_FILTER = "//div[@id='roomGrid']"
    OPT_ROOM_FILTER_OPTION = Locator.xpath("//div[@data-selenium='RoomGridFilter-filter']//div[normalize-space(.)={"
                                           "option}]")

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
