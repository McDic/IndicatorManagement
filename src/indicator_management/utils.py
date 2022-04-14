from typing import Callable, overload

from ._types import Comparable, Numeric, T


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


def wrapped_chained_comparison(
    comparison_func: Callable[[Comparable, Comparable], bool]
):
    """
    Wrapped chained comparison.
    """

    def chained_comparison(*values: Comparable) -> bool:
        """
        Return `values[0] < values[1] < ... < values[-1]`.
        """
        current = values[0]
        for i in range(1, len(values)):
            if comparison_func(current, values[i]):
                current = values[i]
            else:
                return False
        else:
            return True

    return chained_comparison
