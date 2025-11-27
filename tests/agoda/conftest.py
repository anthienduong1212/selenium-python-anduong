import os
import pytest

from core.logging.logging import Logger
from core.utils.json_utils import load_json_as
from tests.agoda.data.booking_data import BookingData
from tests.agoda.data.resolve_booking_date import resolve_booking_date

BOOKING_DATA = os.getenv("BOOKING_JSON")


@pytest.fixture(scope="module")
def all_booking_data():
    """Load the entire booking data JSON file once per module."""
    try:
        raw = load_json_as(BOOKING_DATA, lambda data: data)
        return raw
    except Exception:
        raise ValueError("Cannot load booking data file.")


@pytest.fixture(scope="function")
def booking_data(request, all_booking_data) -> BookingData:
    """
    Fixture to provide specific booking data for a test case ID. The 'request.param' will contain the ID
    """
    test_id = request.param
    if test_id in all_booking_data:
        raw_booking_data = all_booking_data[test_id]

        processed_data = load_json_as(raw_booking_data, BookingData.from_dict)
        return resolve_booking_date(processed_data)
    else:
        raise ValueError(f"Booking data for test ID '{test_id}' not found in JSON file.")


# @pytest.fixture()
# def otp_mailbox():
#     ms = SlurpMailUtil(api_key=os.getenv("MAILSLURP_API_KEY"))
#     inbox_id, email_addr = ms.create_inbox(expires_in_minutes=30)
#     yield {"ms": ms, "inbox_id": inbox_id, "email": email_addr}
