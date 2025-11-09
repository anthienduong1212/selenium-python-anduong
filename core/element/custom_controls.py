from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Optional, Sequence
from datetime import datetime
from functools import partial

from core.element.locators import Locator
from core.element.elements import Element
from core.element.conditions import visible as cond_visible, clickable as cond_clickable
from core.utils.datetime_utils import parse_strict


@dataclass(frozen=True)
class CalendarConfig:
    # ------- ROOT ------------------
    root: Locator

    # ------- CONTROL BUTTON --------
    next_btn: Locator
    prev_btn: Optional[Locator]

    # ------- MONTH CONTAINER -------
    month_containers: Locator
    month_caption_in_container: Locator

    # ------- DATE PICKER -----------
    day_by_data_date: Callable[[str], "Locator"]
    opener: Optional[Locator]
    max_month_hops: int = 24


class Calendar:
    def __init__(self, config: CalendarConfig, desc: str = "CALENDAR"):
        self.cfg = config
        self.desc = desc
        self.full_date_format = os.getenv("CALENDAR_TIME_FORMAT", "%Y-%m-%d")

    # ------- HELPERS -----------
    def _root_ctx(self):
        if self.cfg.root:
            return Element(self.cfg.root).should_be(cond_visible())
        else:
            raise ValueError("Missing root locator")

    @staticmethod
    def _month_index(dt: datetime) -> int:
        return dt.year * 12 + dt.month

    def _parse_date_picker(self, date_str: str) -> datetime:
        return parse_strict(date_str, self.full_date_format)

    def _visible_month_caption(self) -> list[str]:
        root = self._root_ctx()
        containers = root.all(self.cfg.month_containers).should_have_size(2)

        captions = []
        for i in range(containers.size()):
            month = containers.get(i).find(self.cfg.month_caption_in_container).should(cond_visible())
            captions.append(month.text().strip())

        return captions

    def visible_months(self) -> list[datetime]:
        out = []
        for txt in self._visible_month_caption():
            out.append(parse_strict(txt, os.getenv("CALENDAR_MONTH_LABEL_FORMAT", "%B %Y")))
        return out

    def _ensure_open(self):
        if self.cfg.opener:
            # Assume that if calendar is not opened, there were no calendar title display
            containers = self._root_ctx().all(self.cfg.month_containers)
            if containers.size() == 0:
                self._root_ctx().find(self.cfg.opener).should_be(cond_visible()).click()

    def _locate_day(self, target: datetime):
        iso = target.strftime(self.full_date_format)
        if self.cfg.day_by_data_date:
            return self.cfg.day_by_data_date(iso)
        raise ValueError("No day locate strategy provided (day_by_data_date)")

    # ------- ACTION -----------
    def navigate_to(self, target: datetime):
        """Put the month containing 'target' into the viewport using next/prev (if needed)."""
        self._ensure_open()

        months = self.visible_months()
        if not months:
            months = self.visible_months()

        mi_min, mi_max = self._month_index(months[0]), self._month_index(months[-1])
        mi_tgt = self._month_index(target)
        hops = 0

        while not (mi_min <= mi_tgt <= mi_max):
            if hops >= self.cfg.max_month_hops:
                raise RuntimeError(f"{self.desc}: exceeded max_month_hops while navigating")

            if mi_tgt > mi_max:
                self._root_ctx().find(self.cfg.next_btn).should_be(cond_clickable()).click()
            elif self.cfg.prev_btn and mi_tgt < mi_min:
                self._root_ctx().find(self.cfg.prev_btn).should_be(cond_clickable()).click()
            else:
                break

            hops += 1
            months = self.visible_months()
            mi_min, mi_max = self._month_index(months[0]), self._month_index(months[-1])

    def pick(self, date_str: str):
        """
        Select a date (YYYY-MM-DD).
        Automatically navigate the month and click the date.
        """
        target = self._parse_date_picker(date_str)
        self.navigate_to(target)

        day_loc = self._locate_day(target)
        self._root_ctx().find(day_loc).should_be(cond_clickable()).click()
        return self

    def pick_range(self, start_str: str, end_str: str):
        """Select a date range [start, end] (often used on sites that select Check-in / Check-out)."""
        start_dt = self._parse_date_picker(start_str)
        end_dt = self._parse_date_picker(end_str)
        if end_dt < start_dt:
            raise ValueError("end date must be >= start date")

        self.pick(start_str)
        self.pick(end_str)
        return self


