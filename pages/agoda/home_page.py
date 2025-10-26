from pages.base_page import BasePage
from core.element.locators import Locator
from core.utils.browser_utils import BrowserUtils
from core.element.conditions import Condition, visible as cond_visible
from core.utils.datetime_utils import get_current_date, parse_strict
from pages.agoda.enums.occupancies import OccupancyType


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

    CALD_DATEPICKER_CURRENT_MONTH = '//div[contains(@class,"DayPicker-Caption")]'

    # Occupancy Selector and it controls
    BTN_OCCUPANCY_SELECTOR = Locator.xpath("//div[@id='occupancy-selector']//div[@data-selenium={occupancyType}]"
                                           , desc="HOME_PAGE Occupancy Selector")
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

    def select_date(self, date: str):
        """Select date on calendar"""
        dt_target_date = parse_strict(date, "%Y-%m-%d")

        # get_month_label_th(2) select the second month title on Calendar
        dt_current_month = parse_strict(self.get_month_label_th(2), "%B %Y")

        # Date picker parent
        parent = self.el(self.CALD_DATEPICKER).should_be(cond_visible())

        # Date picker element
        date_picker = parent.find(self.CALD_DATEPICKER_DATE(date=date))

        # Next month button
        next_month_button = parent.find(self.CALD_DATEPICKER_NEXT)

        # Define how many times should we click on next button
        delta = self.month_index(dt_current_month) - self.month_index(dt_target_date)
        delta = max(0, min(delta, 24))

        # If target date is not visible, click next month until see but LIMIT number hits
        if not date_picker.exists():
            for _ in range(delta):
                next_month_button.click()

        date_picker.click()

    def select_booking_date(self, checkin_date: str, checkout_date: str):
        # Select check-in date
        self.select_date(checkin_date)

        # Select check-out date
        self.select_date(checkout_date)

    def get_month_label_th(self, order_month: int = 0) -> str:
        """Get the month title display on Calendar"""
        parent = self.el(self.CALD_DATEPICKER)

        calendar = (parent.all(self.CALD_DATEPICKER_MONTH_LABELS).should_have_size(2).get(order_month - 1)
                    .should(cond_visible()))

        current_month = (calendar.find(self.CALD_DATEPICKER_CURRENT_MONTH)
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










