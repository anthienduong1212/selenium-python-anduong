from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional, Iterable


class AssertionInterface(ABC):
    @abstractmethod
    def assert_equal(self, actual: Any, expected: Any, msg: str) -> None: pass

    @abstractmethod
    def assert_true(self, expr: bool, msg: str) -> None: pass

    @abstractmethod
    def assert_false(self, expr: bool, msg: str) -> None: pass

    @abstractmethod
    def assert_in(self, member: Any, container: Iterable[Any], msg: str) -> None: pass

    @abstractmethod
    def assert_not_in(self, member: Any, container: Iterable[Any], msg: str) -> None: pass

    @abstractmethod
    def assert_len(self, obj: Any, expected_len: int, msg: str) -> None: pass

    @abstractmethod
    def assert_between(self, num: float, lo: float, hi: float, inclusive: bool = True,
                       msg: Optional[str] = None) -> None: pass







