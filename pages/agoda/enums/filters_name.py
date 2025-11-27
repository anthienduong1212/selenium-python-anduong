try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum


class FiltersName(StrEnum):
    ROOM_AMENITIES = "Room amenities"
    PROPERTIES_FACILITIES = "Property facilities"
    ROOM_OFFERS = "Room offers"
    BED_TYPES = "Bed type"
