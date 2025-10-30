from pages.agoda.home_page import HomePage
from pages.agoda.result_page import ResultPage
from pages.agoda.hotel_details import HotelDetails
from pages.agoda.login_page import LoginPage
from pages.agoda.enums.occupancies import OccupancyType
from pages.agoda.enums.detailed_navbar_options import NavbarOptions
from core.report.reporting import AllureReporter as AR


def test_homepage(driver, booking):
    home_page = HomePage()
    result_page = ResultPage()
    hotel_detail_page = HotelDetails()

    AR.set_title("Search and filter hotels successfully")

    with AR.step("Navigate to Agoda"):
        home_page.open("https://www.agoda.com")
        AR.attach_text("URL", "https://www.agoda.com")

    with AR.step(f"Search for hotel in {booking.destination}"):
        home_page.search_for_hotel(booking)

    with AR.step(f"Verify that Search Result is displayed correctly with first 5 hotels ({booking.destination})"):
        hotel_list_infor = result_page.get_top_n_hotels(5, booking.destination)
        empty_names, mismatches = result_page.get_missing_data(hotel_list_infor, booking.destination)
        assert not empty_names, f"Missing name hotel at index: {empty_names}"
        assert not mismatches, f"Hotel with mismatched city '{city}' at: {mismatches}"

    with (AR.step(f"Filter the hotels with breakfast included and select the first hotel")):
        result_page.search_filter_with_term("RoomOffers", "Breakfast included")
        first_hotel_infor = result_page.get_top_n_hotels(1, booking.destination)
        result_page.select_first_hotel()

    with AR.step(f"Verify that the hotel detailed page is displayed with correct info"):
        hotel_detail_page.select_navbar_option(NavbarOptions.ROOMS)
        assert hotel_detail_page.is_option_display("Breakfast included"), "Hotel doesn't contain this option"



