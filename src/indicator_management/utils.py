from typing import Callable, overload

from ._types import Numeric, T


@overload
def wrapped_summation() -> Callable[..., Numeric]:
    ...


@overload
def wrapped_summation(start: T) -> Callable[..., T]:
    ...


def wrapped_summation(start=0):
    """
    Wrapped summation function.
    """

    def inner_summation(*values: T) -> T:
        return sum(values, start=start)

    return inner_summation


@overload
def wrapped_multiplication() -> Callable[..., Numeric]:
    ...


@overload
def wrapped_multiplication(start: T) -> Callable[..., T]:
    ...


def wrapped_multiplication(start=1):
    """
    Wrapped multiplication function.
    """

    def inner_multiplication(*values: T) -> T:
        result = start
        for number in values:
            result *= number
        return result

    return inner_multiplication
