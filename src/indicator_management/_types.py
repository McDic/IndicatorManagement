from numbers import Number
from typing import Any, Callable, Protocol, SupportsFloat, TypeVar, Union

T = TypeVar("T")
Numeric = Union[Number, SupportsFloat]

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
