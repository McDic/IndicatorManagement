from typing import Any, Callable, Generator, overload

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


def chained_keyword_and(*values: Any) -> Any:
    """
    Return `values[0] and values[1] and ... and values[-1]`.
    """
    current = values[0]
    for i in range(1, len(values)):
        if not current:
            break
        current = current and values[i]
    return current


def chained_keyword_or(*values: Any) -> Any:
    """
    Return `values[0] or values[1] or ... or values[-1]`.
    """
    current = values[0]
    for i in range(1, len(values)):
        if current:
            break
        current = current or values[i]
    return current


def wrapped_chained_general_operation(
    binary_func: Callable[[Any, Any], Any]
) -> Callable[..., Any]:
    """
    Wrapped chained general operation.
    """

    def chained_general_operation(*values: Any) -> Any:
        current = values[0]
        for i in range(1, len(values)):
            current = binary_func(current, values[i])
        return current

    return chained_general_operation


def range_forever(start: int = 0, step: int = 1) -> Generator[int, None, None]:
    """
    Similar to range, but produces integers forever.
    """
    now = start
    while True:
        yield now
        now += step
