from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import locale

locale.setlocale(locale.LC_TIME, "en_US.UTF-8")

DEFAULT_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


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


