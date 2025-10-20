try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum


class NavbarOptions(StrEnum):
    OVERVIEWS = "Overviews"
    ROOMS = "Rooms"
    TRIP_RECOMMENDATIONS = "Trip recommendations"
    HOST = "Host"
    FACILITIES = "Facilities"
