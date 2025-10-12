from pages.base_page import BasePage
from core.element.locators import Locator
from selenium.webdriver.common.by import By
from core.configs.config import Configuration
from core.utils.browser_utils import BrowserUtils
from core.element.conditions import Condition, visible as cond_visible
from core.utils.datetime_utils import get_current_date, parse_strict
from pages.agoda.enums.occupancies import OccupancyType


class HomePage(BasePage):
    def __init__(self, config: Configuration):
        super().__init__()
        self.config = config
    # Search box and auto suggest
    TXT_AUTOCOMPLETE_INPUT = Locator.xpath('//div[@id="autocomplete-box"]//input', desc="Search box")
    OPT_AUTOSUGGEST_ITEM = Locator.xpath('//li[@data-selenium="autosuggest-item" and @data-text={city}]', desc="Auto suggest")

    # Date Picker
    CALD_DATEPICKER_DATE = Locator.xpath('//div[@id="DatePicker__AccessibleV2"]//span[@data-selenium-date={date}]', desc="Date Picker")
    CALD_DATEPICKER_NEXT = Locator.xpath("//div[@id='DatePicker__AccessibleV2']//button[@data-selenium='calendar-next-month-button']",
        desc="Next Month")
    CALD_DATEPICKER_CURRENT_MONTH = Locator.xpath('//div[@id="DatePicker__AccessibleV2"]//div[contains(@class,"DayPicker-Months")]/div',
        desc="Current Month")

    # Occupancy Selector and it controls
    BTN_OCCUPANCY_SELECTOR = Locator.xpath("//div[@id='occupancy-selector']//div[@data-selenium={occupancyType}]", desc="Occupancy Selector")
    BTN_QUANTITY_CONTROL = Locator.xpath(".//button[@data-selenium={control}]", desc="Increase/Decrease")
    BTN_QUANTITY_NUMBER = Locator.xpath(".//div[contains(@data-selenium,'desktop-occ')]")

    # Search button
    BTN_SEARCH = Locator.xpath("//div[@id='Tabs-Container']//button[@data-selenium='searchButton']")

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

    def select_date(self, date: str):
        """Select date on calendar"""
        dt_target_date = parse_strict(date, "%Y-%m-%d")

        # get_current_month(1) select the second month title on Calendar
        dt_current_month = parse_strict(self.get_current_month(1), "%B %Y")

        # Date picker element
        date_picker = self.el(self.CALD_DATEPICKER_DATE(date=date)).should_be(cond_visible())

        # Next month button
        next_month_button = self.el(self.CALD_DATEPICKER_NEXT)

        # Define how many times should we click on next button
        delta = self.month_index(dt_current_month) - self.month_index(dt_target_date)
        delta = max(0, min(delta, 24))

        # If target date is not visible, click next month until see but LIMIT number hits
        if date_picker.exists():
            for _ in range(delta):
                next_month_button.click()

        date_picker.click()

    def select_booking_date(self, checkin_date: str, checkout_date: str):
        # Select check-in date
        self.select_date(checkin_date)

        # Select check-out date
        self.select_date(checkout_date)

    def get_current_month(self, order_month: int = 0) -> str:
        """Get the month title display on Calendar"""
        calendar = self.els(self.CALD_DATEPICKER_CURRENT_MONTH).should_have_size(2).get(order_month).should(cond_visible())
        current_month = (calendar.find(Locator.xpath('.//div[contains(@class,"DayPicker-Caption")]'))
                         .should(cond_visible()))
        return current_month.text()

    def month_index(self, d):
        return d.year * 12 + d.month

    def sign_and_abs(self, x: int) -> tuple[str, int]:
        return ("minus", -x) if x < 0 else (("plus", x) if x > 0 else ("zero", 0))

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
        target_quantity = self.sign_and_abs(number - current_quantity)

        # Define the control and number of click
        control, quantity = target_quantity

        # Find the control
        occupancy_control = occupancy_selector.find(self.BTN_QUANTITY_CONTROL(control=control))

        for _ in range(quantity):
            occupancy_control.should_be(cond_visible()).click()

    def click_search(self):
        search_button = self.el(self.BTN_SEARCH).should_be(cond_visible())
        BrowserUtils.click_open_and_switch(lambda: search_button.click())










