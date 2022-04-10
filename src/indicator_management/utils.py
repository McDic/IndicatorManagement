from typing import TypeVar

T = TypeVar("T")


def summation(*numbers: T, start=0) -> T:
    """
    Wrapped summation function.
    """
    return sum(numbers, start=start)


def multiply(*numbers: T, start=1) -> T:
    """
    Wrapped multiplication function.
    """
    result = start
    for number in numbers:
        result *= number
    return result
