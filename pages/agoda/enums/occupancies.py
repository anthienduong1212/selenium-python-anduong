try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum


class OccupancyType(StrEnum):
    OCCUPANCY_ROOM = "occupancyRoom"
    OCCUPANCY_ADULTS = "occupancyAdults"
    OCCUPANCY_CHILDREN = "occupancyChildren"
