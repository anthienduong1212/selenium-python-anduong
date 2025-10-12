from pages.agoda.home_page import HomePage
from pages.agoda.result_page import ResultPage
from pages.page_factory import PageFactory
from pages.agoda.enums.occupancies import OccupancyType


def test_homepage(driver):
    page_factory = PageFactory()

    home_page = page_factory.create(HomePage)
    result_page = page_factory.create(ResultPage)

    home_page.open("https://www.agoda.com")

    home_page.enter_text_in_autocomplete("Dalat")
    home_page.select_auto_suggest_item("Dalat")
    home_page.select_booking_date("2025-11-01", "2025-11-30")
    home_page.enter_number_of_occupancy(OccupancyType.OCCUPANCY_ADULTS, 2)
    home_page.click_search()

    result_page.verify_top_n_hotels_are_in_city(5, "Dalat")



