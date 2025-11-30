try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum


class FiltersName(StrEnum):
    ROOM_AMENITIES = "RoomAmenities"
    PROPERTIES_FACILITIES = "Facilities"
    ROOM_OFFERS = "RoomOffers"
    BED_TYPES = "BedType"
