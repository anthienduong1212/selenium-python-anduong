from pages.agoda.home_page import HomePage
from pages.agoda.result_page import ResultPage
from pages.agoda.hotel_details import HotelDetails
from pages.agoda.enums.occupancies import OccupancyType
from pages.agoda.enums.detailed_navbar_options import NavbarOptions


def test_homepage(driver):

    home_page = HomePage()
    result_page = ResultPage()
    hotel_detail_page = HotelDetails()

    home_page.open("https://www.agoda.com")

    home_page.enter_text_in_autocomplete("Dalat")
    home_page.select_auto_suggest_item("Dalat")
    home_page.select_booking_date("2025-11-01", "2025-11-30")
    home_page.enter_number_of_occupancy(OccupancyType.OCCUPANCY_ADULTS, 2)
    home_page.click_search()

    result_page.verify_top_n_hotels_are_in_city(5, "Dalat")
    result_page.search_filter_with_term("RoomOffers", "Breakfast included")
    result_page.select_first_hotel()

    hotel_detail_page.select_navbar_option(NavbarOptions.ROOMS)
    assert hotel_detail_page.is_option_display("Breakfast included"), "Hotel doesn't contain this option"
