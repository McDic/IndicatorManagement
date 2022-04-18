from __future__ import annotations

from numbers import Number
from typing import (
    Any,
    Callable,
    Protocol,
    SupportsAbs,
    SupportsFloat,
    SupportsInt,
    SupportsRound,
    TypeVar,
)

T = TypeVar("T")
S = TypeVar("S")
R = TypeVar("R")


class BoundMethod(Protocol[S, R]):
    """
    Represents bound method. Used for typing hints.
    """

    __func__: Callable[..., R]
    __self__: S

    def __call__(self, *args: Any, **kwargs: Any) -> R:
        ...


class Comparable(Protocol):
    """
    Represents comparable object, but without `__eq__` and `__ne__`.
    """

    def __lt__(self, other) -> bool:
        ...

    def __le__(self, other) -> bool:
        ...

    def __gt__(self, other) -> bool:
        ...

    def __ge__(self, other) -> bool:
        ...


class SupportsEqual(Protocol):
    """
    Represents object which supports `==` and `!=`.
    """

    def __eq__(self, other) -> bool:
        ...

    def __ne__(self, other) -> bool:
        ...


class Numeric(
    Comparable,
    SupportsEqual,
    SupportsInt,
    SupportsFloat,
    SupportsRound,
    SupportsAbs,
    Number,
):
    """
    Represents numerical data types.
    """

    def __add__(self, other) -> Numeric:
        ...

    def __radd__(self, other) -> Numeric:
        ...

    def __sub__(self, other) -> Numeric:
        ...

    def __rsub__(self, other) -> Numeric:
        ...

    def __mul__(self, other) -> Numeric:
        ...

    def __rmul__(self, other) -> Numeric:
        ...

    def __truediv__(self, other) -> Numeric:
        ...

    def __rtruediv__(self, other) -> Numeric:
        ...

    def __pow__(self, other) -> Numeric:
        ...

    def __rpow__(self, other) -> Numeric:
        ...

    def __bool__(self) -> bool:
        ...

    def __pos__(self) -> Numeric:
        ...

    def __neg__(self) -> Numeric:
        ...

    def __floor__(self) -> int:
        ...

    def __ceil__(self) -> int:
        ...


class ComparisonFunc(Protocol):
    """
    Represents comparison function.
    """

    def __call__(self, arg1: Any, arg2: Any) -> bool:
        ...
