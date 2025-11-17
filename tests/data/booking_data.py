from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from pages.agoda.enums.occupancies import OccupancyType, pairs_from_dict


@dataclass(frozen=True)
class BookingData:
    destination: str
    checkin_date: str
    checkout_date: str
    occupancies: Dict[str, str]

    @staticmethod
    def from_dict(d: Dict) -> "BookingData":
        occ = d.get("occupancies") or {}
        occupancy_room = max(int(occ.get("occupancyRooms", 0) or 0), 0)
        occupancy_children = max(int(occ.get("occupancyChildren", 0) or 0), 0)
        occupancy_adults = max(int(occ.get("occupancyAdults", 0) or 0), 0)

        return BookingData(
            destination=d["destination"],
            checkin_date=d["checkin_date"],
            checkout_date=d["checkout_date"],
            occupancies={"occupancyRooms": occupancy_room,
                         "occupancyChildren": occupancy_children,
                         "occupancyAdults": occupancy_adults},
        )

    @property
    def occ_pairs(self) -> List[Tuple[OccupancyType], int]:
        return pairs_from_dict(self.occupancies)
