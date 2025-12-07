import os
import pytest

from core.report.reporting import AllureReporter as AR
from core.utils.string_utils import contains_text
from pages.agoda.enums.detailed_navbar_options import NavbarOptions
from pages.agoda.enums.occupancies import OccupancyType
from pages.agoda.enums.filters_name import FiltersName
from pages.agoda.home_page import HomePage
from pages.agoda.hotel_details import HotelDetails
from pages.agoda.login_page import LoginPage
from pages.agoda.result_page import ResultPage
from tests.agoda.data.booking_data import BookingData

BASE_URL = os.getenv("BASE_URL")


class TestBooking:

    @pytest.mark.parametrize("booking_data", ["test_tc01"], indirect=True)
    def test_tc01(self, booking_data: BookingData, hard_asserts, soft_asserts):
        home_page = HomePage()
        result_page = ResultPage()
        hotel_detail_page = HotelDetails()

        AR.set_title("Search and filter hotels successfully")

        home_page.open(BASE_URL)
        home_page.search_for_hotel(booking_data)

        mismatches = result_page.checking_hotel_address_from_search(5, booking_data.destination)
        hard_asserts.assert_len(mismatches, 0, "Verify that there is no hotel with mismatched destination")

        result_page.filter_with_term(FiltersName.ROOM_OFFERS, booking_data.filters)

        hotel_infor = result_page.get_search_hotel_results(1)[0]
        result_page.select_first_hotel()

        soft_asserts.assert_true(hotel_detail_page.is_option_display(FiltersName.ROOM_OFFERS, booking_data.filters),
                                 "Verify that hotel room offer this service")

        soft_asserts.assert_true(hotel_detail_page.is_hotel_information_correct(hotel_infor),
                                 "Verify that hotel information is display correctly")

    @pytest.mark.parametrize("booking_data", ["test_tc02"], indirect=True)
    def test_tc02(self, booking_data: BookingData, hard_asserts, soft_asserts, otp_mailbox):
        home_page = HomePage()
        result_page = ResultPage()
        hotel_detail_page = HotelDetails()
        login_page = LoginPage()

        AR.set_title("Add hotel into Favourite successfully")

        home_page.open(BASE_URL)
        home_page.search_for_hotel(booking_data)

        mismatches = result_page.checking_hotel_address_from_search(5, booking_data.destination)
        hard_asserts.assert_len(mismatches, 0, "Verify that there is no hotel with mismatched destination")

        result_page.filter_with_term(FiltersName.PROPERTIES_FACILITIES, booking_data.filters)

        hotel_infor = result_page.get_search_hotel_results(1)[0]
        result_page.select_first_hotel()

        soft_asserts.assert_true(hotel_detail_page.is_hotel_information_correct(hotel_infor),
                                 "Verify that hotel information is display correctly")

        soft_asserts.assert_true(hotel_detail_page.is_option_display(FiltersName.PROPERTIES_FACILITIES,
                                                                     booking_data.filters),
                                 "Verify that hotel room offer this service")

        login_page.login_with_otp(otp_mailbox)

        hotel_detail_page.add_to_favorites()
