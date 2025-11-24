import os
import pytest

from core.assertion.assertion import assert_equal, assert_len, assert_true
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

    mismatches = result_page.checking_hotel_address_from_search(5, booking_data.destination)
    assert_true(mismatches, f"Verify that there is no hotel with mismatched city")

    result_page.search_filter_with_term("RoomOffers", "Breakfast included")
    first_hotel_infor = result_page.get_search_hotel_results(1, booking_data.destination)
    result_page.select_first_hotel()

    actual = hotel_detail_page.get_hotel_information()
    expected = first_hotel_infor[0]

    actual_name = actual.get("name")
    expected_name = expected.get("name")

    assert_equal(actual_name, expected_name,
                 f"Hotel Name doesn't match | ACTUAL: {actual_name} | EXPECTED: {expected_name}")

    actual_addr = actual.get("address")
    expected_addr = expected.get("address")

    assert_true(contains_text(actual_addr, expected_addr),
                f"Hotel Address doesn't match | ACTUAL: {actual_addr} | EXPECTED: {expected_addr}")

    assert_true(hotel_detail_page.is_option_display("Breakfast included"), "Hotel doesn't contain this option")
