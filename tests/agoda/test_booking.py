import os
import pytest

from core.assertion.assertion import assert_equal, assert_false, assert_true
from core.report.reporting import AllureReporter as AR
from core.utils.string_utils import contains_text
from pages.agoda.enums.detailed_navbar_options import NavbarOptions
from pages.agoda.enums.occupancies import OccupancyType
from pages.agoda.home_page import HomePage
from pages.agoda.hotel_details import HotelDetails
from pages.agoda.login_page import LoginPage
from pages.agoda.result_page import ResultPage

BASE_URL = os.getenv("BASE_URL")


@pytest.mark.usefixtures("driver")
def test_homepage(booking_data):
    home_page = HomePage()
    result_page = ResultPage()
    hotel_detail_page = HotelDetails()

    AR.set_title("Search and filter hotels successfully")

    home_page.open(BASE_URL)

    home_page.search_for_hotel(booking_data)

    with AR.step(f"Verify that Search Result is displayed correctly with first 5 hotels ({booking_data.destination})"):
        hotel_list_infor = result_page.get_result_of_n_hotel(5, booking_data.destination)
        empty_names, mismatches = result_page.get_missing_data(hotel_list_infor, booking_data.destination)
        assert_false(empty_names, f"Missing name hotel at index: {empty_names}")
        assert_false(mismatches, f"Hotel with mismatched city at: {mismatches}")

    with (AR.step(f"Filter the hotels with breakfast included and select the first hotel")):
        result_page.search_filter_with_term("RoomOffers", "Breakfast included")
        first_hotel_infor = result_page.get_result_of_n_hotel(1, booking_data.destination)[0]
        result_page.select_first_hotel()

    with AR.step(f"Verify that the hotel detailed page is displayed with correct info"):
        actual = hotel_detail_page.get_hotel_information()
        expected = first_hotel_infor

        actual_name = actual.get("name")
        expected_name = expected.get("name")

        assert_equal(actual_name, expected_name,
                     f"Hotel Name doesn't match | ACTUAL: {actual_name} | EXPECTED: {expected_name}")

        actual_addr = actual.get("address")
        expected_addr = expected.get("address")
        assert_true(contains_text(actual_addr, expected_addr),
                    f"Hotel Address doesn't match | ACTUAL: {actual_addr} | EXPECTED: {expected_addr}")

        hotel_detail_page.select_navbar_option(NavbarOptions.ROOMS)
        assert_true(hotel_detail_page.is_option_display("Breakfast included"), "Hotel doesn't contain this option")



