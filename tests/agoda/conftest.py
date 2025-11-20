import os
import pytest

from core.logging.logging import Logger
from core.utils.json_utils import load_json_as
from tests.agoda.data.booking_data import BookingData
from tests.agoda.data.resolve_booking_date import resolve_booking_date

BOOKING_DATA = os.getenv("BOOKING_JSON")


@pytest.fixture(scope="module")
def booking_data() -> BookingData:
    """Fixture to load  booking data."""
    try:
        raw = load_json_as(BOOKING_DATA, BookingData.from_dict)
        return resolve_booking_date(raw)
    except Exception:
        raise ValueError("Data Path is NULL")


# @pytest.fixture()
# def otp_mailbox():
#     ms = SlurpMailUtil(api_key=os.getenv("MAILSLURP_API_KEY"))
#     inbox_id, email_addr = ms.create_inbox(expires_in_minutes=30)
#     yield {"ms": ms, "inbox_id": inbox_id, "email": email_addr}
