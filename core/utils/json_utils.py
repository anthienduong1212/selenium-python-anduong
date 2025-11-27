from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Type, TypeVar, Union

from core.logging.logging import Logger

T = TypeVar("T")


def load_json_as(path_or_data: Union[str, Path, dict], from_dict: Callable[[dict], T]) -> T:
    """
    Loads JSON data either from a file path or from an existing dictionary,
    then maps it using the from_dict function.
    """
    data_dict = dict[str, Any]

    if isinstance(path_or_data, (str, Path)):
        with open(path_or_data, "r", encoding="utf-8") as f:
            data_dict = json.load(f)

    elif isinstance(path_or_data, dict):
        data_dict = path_or_data

    else:
        raise TypeError("Input must be a file path (str/Path) or a dictionary (dict)")

    return from_dict(data_dict)


def convert_dict_to_pairs(d: Dict[str, Any], key_converter: Callable[[str], T]) -> List[Tuple[T, Any]]:
    """
        Converts a dictionary to a list of (converted key, value) pairs.
    :param d: Input Dict
    :param key_converter: A function that can be called,
                        takes a string (key of the dictionary) and returns a desired data type (T)
    :return: A list of tuple pairs, with the keys transformed.
    """
    return [(key_converter(k), v) for k, v in d.items()]
