from numbers import Number
from typing import Any, Callable, Protocol, SupportsFloat, TypeVar, Union

Numeric = Union[Number, SupportsFloat]

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


class ComparisonFunc(Protocol):
    """
    Represents comparison function.
    """

    def __call__(self, arg1: Any, arg2: Any) -> bool:
        ...
