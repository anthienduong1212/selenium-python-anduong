from __future__ import annotations
import unicodedata
from core.logging.logging import Logger


def normalize(s: str) -> str:
    """Normalize text: eliminate vietnamese sign, lower, space-trim (compare 'Đà Lạt' ~ 'Da Lat' ~ 'Dalat')."""
    Logger.debug(f"Normalizing string: {s}")
    try:
        s = unicodedata.normalize("NFKD", s)
        normalized = " ".join(ch for ch in s if not unicodedata.combining(ch)).lower().strip()
        Logger.debug(f"Normalized string: {normalized}")
        return normalized
    except Exception as e:
        Logger.error(f"Error normalizing string: {e}")
        raise


def contains_text(text: str, ex: str) -> bool:
    """Verify text contain city (tolerant 'da lat' ~ 'dalat')."""
    t = normalize(text).replace(" ", "")
    c = normalize(ex).replace(" ", "")
    Logger.debug(f"Verify {t} contains {c}")
    return c in t


def sign_and_abs(x: int) -> tuple[str, int]:
    return ("minus", -x) if x < 0 else (("plus", x) if x > 0 else ("zero", 0))
