from pages.base_page import BasePage
from core.element.locators import Locator
from core.element.custom_controls import Calendar, CalendarConfig
from core.utils.browser_utils import BrowserUtils
from core.element.conditions import visible as cond_visible
from core.utils.datetime_utils import parse_strict
from core.utils.string_utils import sign_and_abs

from pages.agoda.enums.occupancies import OccupancyType
from tests.data.booking_data import BookingData


class HomePage(BasePage):
    def __init__(self):
        super().__init__()

    # Search box and auto suggest
    TXT_AUTOCOMPLETE_INPUT = Locator.xpath('//div[@id="autocomplete-box"]//input', desc="HOME_PAGE Search box")
    OPT_AUTOSUGGEST_ITEM = Locator.xpath('//li[@data-selenium="autosuggest-item" and @data-text={city}]',
                                         desc="HOME_PAGE Auto suggest")

    # Date Picker
    CALD_DATEPICKER = '//div[@id="DatePicker__AccessibleV2"]'
    CALD_DATEPICKER_DATE = Locator.xpath('//span[@data-selenium-date={date}]', desc="HOME_PAGE Date Picker")
    CALD_DATEPICKER_NEXT = Locator.xpath("//button[@data-selenium='calendar-next-month-button']",
        desc="HOME_PAGE Next Month Button")
    CALD_DATEPICKER_MONTH_LABELS = Locator.xpath('//div[contains(@class,"DayPicker-Months")]/div',
        desc="HOME_PAGE Month Label")

    CALD_DATEPICKER_CURRENT_MONTH = Locator.xpath('//div[contains(@class,"DayPicker-Caption")]',
                                                  "HOME_PAGE Current month")

    # Occupancy Selector and it controls
    BTN_OCCUPANCY_SELECTOR = Locator.xpath("//div[@id='occupancy-selector']//div[@data-selenium={occupancyType}]")
    BTN_QUANTITY_CONTROL = Locator.xpath(".//button[@data-selenium={control}]", desc="HOME_PAGE Increase/Decrease")
    BTN_QUANTITY_NUMBER = Locator.xpath(".//div[contains(@data-selenium,'desktop-occ')]", desc="HOME_PAGE Current "
                                                                                               "Quantity")

    # Search button
    BTN_SEARCH = Locator.xpath("//div[@id='Tabs-Container']//button[@data-selenium='searchButton']"
                               , "HOME_PAGE Search Button")

    def enter_text_in_autocomplete(self, text: str):
        """Fill text to search text box"""
        search_box = self.el(self.TXT_AUTOCOMPLETE_INPUT)
        search_box.type(text, True)
        return self

    def select_auto_suggest_item(self, city: str):
        """Select an option from auto suggest"""
        suggest_item = self.el(self.OPT_AUTOSUGGEST_ITEM(city=city))
        suggest_item.click()
        return self

    def select_booking_date(self, checkin_date: str, checkout_date: str):
        calendar_config = CalendarConfig(
            root=self.CALD_DATEPICKER,
            next_btn=self.CALD_DATEPICKER_NEXT,
            prev_btn=None,
            month_containers=self.CALD_DATEPICKER_MONTH_LABELS,
            month_caption_in_container=self.CALD_DATEPICKER_CURRENT_MONTH,
            day_by_data_date=lambda date: self.CALD_DATEPICKER_DATE(date=date),
            opener=None,
            max_month_hops=24,
        )
        calendar = Calendar(calendar_config, "AGODA CALENDAR")
        calendar.pick_range(checkin_date, checkout_date)

    def enter_number_of_occupancy(self, occ_type: OccupancyType, number: int):
        """
        Enter number of occupancy, has ability to verify zero value
        :param occ_type: Occupancy type such as Room, Adults, Children
        :param number: number of this occupancy
        """
        # Find occupancy by type
        occupancy_selector = self.el(self.BTN_OCCUPANCY_SELECTOR(occupancyType=occ_type)).should_be(cond_visible())
        # Get current quantity display on current occupancy
        occupancy_quantity = occupancy_selector.find(self.BTN_QUANTITY_NUMBER)

        # Define how many times should we click on +/- button
        current_quantity = int(occupancy_quantity.text())
        target_quantity = sign_and_abs(number - current_quantity)

        # Define the control and number of click
        control, quantity = target_quantity

        # Find the control
        occupancy_control = occupancy_selector.find(self.BTN_QUANTITY_CONTROL(control=control))

        for _ in range(quantity):
            occupancy_control.should_be(cond_visible()).click()

    def click_search(self):
        search_button = self.el(self.BTN_SEARCH)
        BrowserUtils.click_open_and_switch(lambda: search_button.click())

    def search_for_hotel(self, booking: BookingData):
        self.enter_text_in_autocomplete(booking.destination)
        self.select_auto_suggest_item(booking.destination)
        self.select_booking_date(booking.checkin_date, booking.checkout_date)
        for enum_val, count in booking.occ_pairs:
            self.enter_number_of_occupancy(enum_val, count)

        self.click_search()










