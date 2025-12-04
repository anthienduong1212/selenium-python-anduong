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

        hotel_infor = result_page.get_search_hotel_results(1, booking_data.destination)
        result_page.select_first_hotel()

        actual = hotel_detail_page.get_hotel_information()
        expected = hotel_infor[0]

        actual_name = actual.get("name")
        expected_name = expected.get("name")

        hard_asserts.assert_equal(actual_name, expected_name, "Verify that hotel name is display correctly")

        actual_addr = actual.get("address")
        expected_addr = expected.get("address")

        soft_asserts.assert_true(contains_text(actual_addr, expected_addr),
                                 "Verify that hotel address is display correctly")

        soft_asserts.assert_true(hotel_detail_page.is_option_display("Breakfast included"),
                                 "Verify that hotel room offer this service")

    @pytest.mark.parametrize("booking_data", ["test_tc02"], indirect=True)
    def test_tc02(self, booking_data: BookingData, hard_asserts, soft_asserts, otp_mailbox):
        home_page = HomePage()
        result_page = ResultPage()
        hotel_detail_page = HotelDetails()
        login_page = LoginPage()

        AR.set_title("Add hotel into Favourite successfully")

        home_page.open("https://www.agoda.com/account/signin.html?ottoken=eyJhbGciOiJBMjU2S1ciLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIn0.-MODPHziOtpDoxBxXcU_gWV2rfXzJrsqe06WMPZM1nXl7-HoSQMv5dQLINjARq-lM8YWB-3daEg66ky2K4vXarXS51RWuNvV.ILExfiyTJWj4a9IaKsr0kA.u0Q0KvghcY-ne40Hadnq126Mv2A-qgRAwXq9qmwPTv59IlcDIP6M2g40kSjsmYEZ.yw5EpnhMdeYE3fx1migUEgwoKuudK-qkjgtPXsdcPoc&returnurl=%2Fpagenotfound.html")

        # home_page.open(BASE_URL)
        # home_page.search_for_hotel(booking_data)
        #
        # mismatches = result_page.checking_hotel_address_from_search(5, booking_data.destination)
        # hard_asserts.assert_len(mismatches, 0, "Verify that there is no hotel with mismatched destination")
        #
        # result_page.filter_with_term(FiltersName.PROPERTIES_FACILITIES, booking_data.filters)
        #
        # hotel_infor = result_page.get_search_hotel_results(1, booking_data.destination)
        # result_page.select_first_hotel()
        #
        # actual = hotel_detail_page.get_hotel_information()
        # expected = hotel_infor[0]
        #
        # actual_name = actual.get("name")
        # expected_name = expected.get("name")
        #
        # hard_asserts.assert_equal(actual_name, expected_name, "Verify that hotel name is display correctly")
        #
        # actual_addr = actual.get("address")
        # expected_addr = expected.get("address")
        #
        # soft_asserts.assert_true(contains_text(actual_addr, expected_addr),
        #                          "Verify that hotel address is display correctly")
        #
        # soft_asserts.assert_true(hotel_detail_page.is_option_display("Swimming pool"),
        #                          "Verify that hotel room offer this service")
        #
        # hotel_detail_page.add_to_favorites()

        email_address: str = otp_mailbox["email"]
        inbox_id: str = otp_mailbox["inbox_id"]
        ms = otp_mailbox["ms"]

        login_page.login(email_address)
        login_page.submit_otp_from_email(ms, inbox_id, email_address)







