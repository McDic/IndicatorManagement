from __future__ import annotations
from numbers import Number
from typing import Any, Generator, Generic, Iterable, Iterator, Optional, TypeVar


T = TypeVar("T")


class AbstractIndicator(Generic[T]):
    """
    Abstract class of all indicators.
    """

    def __init__(
        self,
        *,
        default_value: Optional[T] = None,
        pre_requisites: Iterable[AbstractIndicator] = (),
    ) -> None:
        self._default_value = default_value
        self.indicator: Optional[T] = default_value
        self._post_dependencies: list[AbstractIndicator] = []

        pre_requisites = list(pre_requisites)
        self._pre_requisites_trigger: dict[AbstractIndicator, bool] = {
            pre_requisite: False for pre_requisite in pre_requisites
        }
        self._pre_requisites_values: dict[AbstractIndicator, Any] = {
            pre_requisite: pre_requisite.indicator for pre_requisite in pre_requisites
        }
        self._pre_requisite_counter: int = len(pre_requisites)
        for pre_requisite in self._pre_requisites_trigger:
            pre_requisite._post_dependencies.append(self)

    # =================================================================================
    # Arithmetic operations

    def __add__(self, other) -> SummationIndicator:
        if isinstance(other, AbstractIndicator):
            return SummationIndicator(self, other)
        elif isinstance(other, Number):
            return SummationIndicator(self, ConstantIndicator(default_value=other))
        else:
            raise TypeError

    def __radd__(self, other) -> SummationIndicator:
        return self.__add__(other)

    def __iadd__(self, other):
        raise NotImplementedError

    def __sub__(self, other) -> SummationIndicator:
        return self + -other

    def __rsub__(self, other) -> SummationIndicator:
        return -self + other

    def __isub__(self, other):
        raise NotImplementedError

    def __mul__(self, other) -> MultiplicationIndicator:
        if isinstance(other, AbstractIndicator):
            return MultiplicationIndicator(self, other)
        elif isinstance(other, Number):
            return MultiplicationIndicator(self, ConstantIndicator(default_value=other))
        else:
            raise TypeError

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        raise NotImplementedError

    def __truediv__(self, other) -> MultiplicationIndicator:
        if isinstance(other, AbstractIndicator):
            return self * ArithmeticInverseIndicator(other)
        elif isinstance(other, (int, float, complex)):
            return self * (1 / other)
        else:
            raise TypeError

    def __rtruediv__(self, other) -> MultiplicationIndicator:
        return other * ArithmeticInverseIndicator(self)

    def __itruediv__(self, other):
        raise NotImplementedError

    def __pos__(self) -> AbstractIndicator:
        return self

    def __neg__(self) -> MultiplicationIndicator:
        return self * -1

    # =================================================================================
    # Other operations which produces indicators

    def __getitem__(self, index):
        return IndexAccessIndicator(self, index)

    # =================================================================================
    # Extra magic methods

    def __hash__(self) -> int:
        return hash(id(self))

    # =================================================================================
    # Helper APIs

    def get_pre_requisites(self) -> Generator[AbstractIndicator, None, None]:
        yield from self._pre_requisites_trigger.keys()

    def is_basis(self) -> bool:
        """
        Check if this indicator does not require any pre-requisites.
        """
        return not bool(self._pre_requisites_trigger)

    # =================================================================================
    # Update APIs

    def trigger_from_pre_requisite(self, pre_requisite: AbstractIndicator) -> None:
        """
        Receive trigger from pre-requisite of this indicator.
        If condition is satisfied, update current indicator.
        If you give any indicator which is not pre-requisite
        of this indicator, it will raise an `KeyError`.
        """
        self._pre_requisites_values[pre_requisite] = pre_requisite.indicator
        if not self._pre_requisites_trigger[pre_requisite]:
            self._pre_requisites_trigger[pre_requisite] = True
            self._pre_requisite_counter -= 1

        if self._pre_requisite_counter == 0:
            self._pre_requisite_counter = len(self._pre_requisites_trigger)
            self._pre_requisites_trigger = {
                pr: False for pr in self._pre_requisites_trigger
            }
            self.update()

    def update(self) -> None:
        """
        Update current indicator and all dependent indicators.
        """
        self.update_single()
        for dependent_indicator in self._post_dependencies:
            dependent_indicator.trigger_from_pre_requisite(self)

    def update_single(self) -> None:
        """
        Calculate and update new indicator value based on given `sources`.
        """
        raise NotImplementedError


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


class SummationIndicator(AbstractIndicator[T]):
    """
    Summation of indicators.
    """

    def __init__(
        self, *indicators: AbstractIndicator[T], default_value=0, **kwargs
    ) -> None:
        super().__init__(
            pre_requisites=indicators, default_value=default_value, **kwargs
        )

    def update_single(self) -> None:
        if None in self._pre_requisites_values.values():
            self.indicator = None
        else:
            self.indicator = sum(
                self._pre_requisites_values.values(), start=self._default_value
            )


class MultiplicationIndicator(AbstractIndicator[T]):
    """
    Multiplication of indicators.
    """

    def __init__(
        self, *indicators: AbstractIndicator[T], default_value=1, **kwargs
    ) -> None:
        super().__init__(
            pre_requisites=indicators, default_value=default_value, **kwargs
        )

    def update_single(self) -> None:
        if None in self._pre_requisites_values.values():
            self.indicator = None
        else:
            self.indicator = self._default_value
            for value in self._pre_requisites_values.values():
                self.indicator *= value


class ArithmeticInverseIndicator(AbstractIndicator[T]):
    """
    Arithmetic inverse of indicators.
    """

    def __init__(self, indicator: AbstractIndicator[T], *args, **kwargs) -> None:
        super().__init__(
            *args, pre_requisites=(indicator,), default_value=None, **kwargs
        )

    def update_single(self) -> None:
        value = list(self._pre_requisites_values.values())[0]
        self.indicator = 1 / value if value else None


class IndexAccessIndicator(AbstractIndicator[T]):
    """
    Index accessing indicators.
    """

    def __init__(
        self, indicator: AbstractIndicator, index: Any, *args, **kwargs
    ) -> None:
        super().__init__(*args, pre_requisites=(indicator,), **kwargs)
        self._index = index

    def update_single(self) -> None:
        value = list(self._pre_requisites_values.values())[0]
        self.indicator = value[self._index] if value is not None else None
