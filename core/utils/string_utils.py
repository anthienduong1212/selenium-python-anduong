from __future__ import annotations
import unicodedata


def normalize(s: str) -> str:
    """Normalize text: eliminate vietnamese sign, lower, space-trim (compare 'Đà Lạt' ~ 'Da Lat' ~ 'Dalat')."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.lower().split())


def contains_text(text: str, city: str) -> bool:
    """Verify text contain city (tolerant 'da lat' ~ 'dalat')."""
    t = normalize(text).replace(" ", "")
    c = normalize(city).replace(" ", "")
    return c in t
