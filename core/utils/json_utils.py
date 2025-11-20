from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Type, TypeVar

T = TypeVar("T")


def load_json_as(path: str | Path, from_dict: Callable[[dict], T]) -> T:
    with open(path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return from_dict(data)


def convert_dict_to_pairs(d: Dict[str, Any], key_converter: Callable[[str], T]) -> List[Tuple[T, Any]]:
    """
        Converts a dictionary to a list of (converted key, value) pairs.
    :param d: Input Dict
    :param key_converter: A function that can be called,
                        takes a string (key of the dictionary) and returns a desired data type (T)
    :return: A list of tuple pairs, with the keys transformed.
    """
    return [(key_converter(k), v) for k, v in d.items()]
