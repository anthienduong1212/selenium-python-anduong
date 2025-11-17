from __future__ import annotations

from zoneinfo import ZoneInfo

from core.utils.datetime_utils import DEFAULT_TZ, resolve_date_field
from tests.data.booking_data import BookingData


def resolve_booking_date(booking: BookingData, *, tz: ZoneInfo = DEFAULT_TZ) -> BookingData:
    ci = resolve_date_field(booking.checkin_date, tz=tz, fmt="%Y-%m-%d") if booking.checkin_date is not None else None
    co = resolve_date_field(booking.checkout_date, tz=tz, fmt="%Y-%m-%d") if booking.checkout_date is not None else None

    return BookingData(
        destination=booking.destination,
        checkin_date=ci,
        checkout_date=co,
        occupancies=booking.occupancies
    )
