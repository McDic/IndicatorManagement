from typing import Iterable, Iterator

from .abc import AbstractIndicator, T


class RawSeriesIndicator(AbstractIndicator[T]):
    """
    Represents an indicator which is updated by raw value stream.
    """

    def __init__(self, *, raw_values: Iterable[T], **kwargs) -> None:
        super().__init__(pre_requisites=(), **kwargs)
        self._raw_values: Iterator[T] = iter(raw_values)

    def update_single(self) -> None:
        self.indicator = next(self._raw_values)


class ConstantIndicator(AbstractIndicator[T]):
    """
    Represents an constant indicator.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(pre_requisites=(), **kwargs)

    def update_single(self) -> None:
        pass
