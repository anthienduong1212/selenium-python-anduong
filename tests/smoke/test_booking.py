from pages.agoda.home_page import HomePage
from pages.page_factory import PageFactory
from pages.agoda.enums.occupancies import OccupancyType


def test_homepage(driver):
    page_factory = PageFactory()

    home_page = page_factory.create(HomePage)

    home_page.open("https://www.agoda.com")

    home_page.enter_text_in_autocomplete("Dalat")
    home_page.select_auto_suggest_item("Dalat")
    home_page.select_booking_date("2025-11-01", "2025-11-30")
    home_page.enter_number_of_occupancy(OccupancyType.OCCUPANCY_ADULTS, 2)
    home_page.click_search()



