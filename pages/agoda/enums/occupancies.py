try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum

from typing import Dict, List, Tuple

from core.utils.json_utils import convert_dict_to_pairs


class OccupancyType(StrEnum):
    OCCUPANCY_ROOM = "occupancyRooms"
    OCCUPANCY_ADULTS = "occupancyAdults"
    OCCUPANCY_CHILDREN = "occupancyChildren"


_NAME2ENUM = {e.value: e for e in OccupancyType}


def convert_to_occupancy_type(key: str) -> OccupancyType:
    return _NAME2ENUM[key]


def pairs_from_dict(d: Dict[str, int]) -> List[Tuple[OccupancyType, int]]:
    return convert_dict_to_pairs(d, convert_to_occupancy_type)
