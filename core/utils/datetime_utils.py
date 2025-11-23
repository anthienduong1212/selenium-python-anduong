from __future__ import annotations

import locale
import os
import re
from datetime import date, datetime, timedelta
from typing import Dict
from zoneinfo import ZoneInfo

from dateutil.relativedelta import FR, MO, SA, SU, TH, TU, WE, relativedelta

from core.logging.logging import Logger

locale.setlocale(locale.LC_TIME, os.getenv("LOCALE"))

DEFAULT_TZ = ZoneInfo(os.getenv("TIMEZONE"))

_RX_ISO_OFFSET = re.compile(r"^P(?:(\d+)W)?(?:(\d+)D)?$", re.IGNORECASE)

# BASE tokens:
# - "TODAY"
# - "NEXT_<WEEKDAY>"            (e.g: "NEXT_FRIDAY")
# - "<N>_NEXT_<WEEKDAY>"        (e.g: "2_NEXT_WEDNESDAY")
_RX_BASE = re.compile(r"^(?:(\d+)_)?NEXT_([A-Z]+)$")

_WEEKDAY = {
    "MONDAY": MO, "TUESDAY": TU, "WEDNESDAY": WE, "THURSDAY": TH,
    "FRIDAY": FR, "SATURDAY": SA, "SUNDAY": SU,
}


def _add_iso_offset(base: date, offset: str) -> date:
    m = _RX_ISO_OFFSET.fullmatch(offset)
    if not m:
        raise ValueError(f"Unsupported ISO-8601 offset: {offset!r}")
    weeks = int(m.group(1) or 0)
    days = int(m.group(2) or 0)

    return base + timedelta(days=weeks * 7 + days)


def _nth_next_weekday(base: datetime, weekday_token: str, n: int) -> date:
    wd = _WEEKDAY.get(weekday_token)
    if wd is None:
        raise ValueError(f"Unsupported weekday: {weekday_token!r}")

    return base + relativedelta(weekday=wd(+n))


def _resolve_base_token(base_token: str, *, tz: ZoneInfo) -> date:
    s = base_token.strip().upper()
    if s == "TODAY":
        return get_current_date(tz)
    m = _RX_BASE.fullmatch(s)
    if m:
        n = int(m.group(1) or 1)
        week_day = m.group(2)
        return _nth_next_weekday(get_current_date(tz), week_day, n)

    raise ValueError(f"Unsupported base token: {base_token!r}")


def parse_iso_date_str(s: str) -> date:
    return date.fromisoformat(s)


def _resolve_date_token(obj: Dict, *, tz: ZoneInfo = DEFAULT_TZ) -> date:
    """
        Input from json
    :param obj: Dict as { "$date": { "base": "TODAY|NEXT_FRIDAY|2_NEXT_TUESDAY", "offset": "P3D" } }
    :param tz: current timezone
    :return: 'YYYY-MM-DD'
    """
    Logger.debug(f"Resolving date token with input: {obj}")
    try:
        spec = obj["$date"]
        base = _resolve_base_token(spec.get("base", "TODAY"), tz=tz)
        resolved_date = _add_iso_offset(base, spec.get("offset", "P0D"))
        Logger.info(f"Resolved date: {resolved_date}")
        return resolved_date
    except Exception as e:
        Logger.error(f"Error resolving date token: {e}")
        raise


def resolve_date_field(v, *, tz=DEFAULT_TZ, fmt: str, as_date: bool = False):
    if isinstance(v, str):
        d = date.fromisoformat(v)              # 'YYYY-MM-DD' → date
    elif isinstance(v, dict) and "$date" in v:
        d = _resolve_date_token(v, tz=tz)        # TODAY / NEXT_FRIDAY / 2_NEXT_TUESDAY + offset
    else:
        raise ValueError(f"Unsupported date field: {v!r}")

    # 2) Trả về theo nhu cầu gọi
    return d if as_date else d.strftime(fmt)   # '%Y-%m-%d'


def now_str(pattern: str = "%Y-%m-%d", tz: ZoneInfo | None = DEFAULT_TZ) -> str:
    """
   Return current local by Pattern
   :param pattern: formatted by strftime (e.g "%d/%m/%Y", "%Y-%m-%d %H:%M:%S")
   :param tz: TimeZone, default 'ASIA/Ho_Chi_Minh'
   :return: formatted string
   """
    return get_current_date(tz).strftime(pattern)


def parse_strict(date_str: str, pattern: str, tz: ZoneInfo | None = DEFAULT_TZ) -> datetime:
    naive = datetime.strptime(date_str, pattern)
    return naive.replace(tzinfo=tz or ZoneInfo("UTC"))


def add_days_str(days: int, pattern: str = "%Y-%m-%d", tz: ZoneInfo | None = DEFAULT_TZ) -> str:
    """
    Return future day by current day plus offset
    :param days: plus day (negative day if return day in past)
    :param pattern: formatted by strftime (e.g "%d/%m/%Y", "%Y-%m-%d %H:%M:%S")
    :param tz: TimeZone, default 'ASIA/Ho_Chi_Minh'
    :return: formatted string
    """
    dt = datetime.now(tz or ZoneInfo("UTC")) + timedelta(days=days)
    return dt.strftime(pattern)


def format_datetime(dt: datetime, pattern: str = "%Y-%m-%d", tz: ZoneInfo | None = DEFAULT_TZ) -> str:
    if tz:
        dt = dt.astimezone(tz)
    return dt.strftime(pattern)


def get_current_date(tz: ZoneInfo | None = DEFAULT_TZ):
    return datetime.now(tz or ZoneInfo("UTC"))
