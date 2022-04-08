from __future__ import annotations
from numbers import Number
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Protocol,
    SupportsFloat,
    TypeVar,
    Union,
)


T = TypeVar("T")
Numeric = Union[Number, SupportsFloat]
IOPR_co = TypeVar("IOPR_co", covariant=True)


class IndicatorOperationProtocol(Protocol[IOPR_co]):
    def __call__(
        self, *indicator_or_numbers: Union[AbstractIndicator, Numeric]
    ) -> IOPR_co:
        raise NotImplementedError


IAR = TypeVar("IAR")


def indicatorized_arguments(
    func: Callable[..., IAR]
) -> IndicatorOperationProtocol[IAR]:
    """
    Convert a function which accepts indicators or numbers.
    In resulting function, all number arguments will be changed into `ConstantIndicator`.
    """

    def inner_function(*indicator_or_numbers: Union[AbstractIndicator, Numeric]) -> IAR:
        result = []
        for obj in indicator_or_numbers:
            if isinstance(obj, AbstractIndicator):
                result.append(obj)
            elif isinstance(obj, Number):
                result.append(ConstantIndicator(obj))
            else:
                raise TypeError
        return func(*result)

    return inner_function


class AbstractIndicator(Generic[T]):
    """
    Abstract class of all indicators.
    """

    def __init__(
        self, *pre_requisites: AbstractIndicator, default_value: Optional[T]
    ) -> None:
        self._default_value = default_value
        self.indicator: Optional[T] = default_value
        self._post_dependencies: list[AbstractIndicator] = []

        self.pre_requisites: tuple[AbstractIndicator, ...] = pre_requisites
        assert len(self.pre_requisites) == len(set(self.pre_requisites))
        self._pre_requisites_trigger: dict[AbstractIndicator, bool] = {
            pre_requisite: False for pre_requisite in self.pre_requisites
        }
        self._pre_requisite_counter: int = len(self.pre_requisites)
        for pre_requisite in self._pre_requisites_trigger:
            pre_requisite._post_dependencies.append(self)

    # =================================================================================
    # Arithmetic operations

    @indicatorized_arguments
    def __add__(self, other) -> SummationIndicator:
        return SummationIndicator(self, other)

    def __radd__(self, other) -> SummationIndicator:
        return self.__add__(other)

    @indicatorized_arguments
    def __sub__(self, other) -> SubtractionIndicator:
        return SubtractionIndicator(self, other)

    @indicatorized_arguments
    def __rsub__(self, other) -> SubtractionIndicator:
        return SubtractionIndicator(other, self)

    @indicatorized_arguments
    def __mul__(self, other) -> MultiplicationIndicator:
        return MultiplicationIndicator(self, other)

    def __rmul__(self, other):
        return self.__mul__(other)

    @indicatorized_arguments
    def __truediv__(self, other) -> DivisionIndicator:
        return DivisionIndicator(self, other)

    @indicatorized_arguments
    def __rtruediv__(self, other) -> DivisionIndicator:
        return DivisionIndicator(other, self)

    @indicatorized_arguments
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

    def generate_pre_requisite_values(self) -> Generator[Optional[Any], None, None]:
        """
        Generate pre-requisite indicators' values.
        """
        yield from (indicator.indicator for indicator in self.pre_requisites)

    def is_basis(self) -> bool:
        """
        Check if this indicator does not require any pre-requisites.
        """
        return not bool(self.pre_requisites)

    # =================================================================================
    # Update APIs

    def trigger_from_pre_requisite(self, pre_requisite: AbstractIndicator) -> None:
        """
        Receive trigger from pre-requisite of this indicator.
        If condition is satisfied, update current indicator.
        If you give any indicator which is not pre-requisite
        of this indicator, it will raise an `ValueError`.
        """
        if pre_requisite not in self._pre_requisites_trigger:
            raise ValueError("Given pre-requisite is not available in this indicator")

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


AI = TypeVar("AI", bound=AbstractIndicator)


def none_if_none_in_pre_requisites(
    method: Callable[[AI], None]
) -> Callable[[AI], None]:
    """
    Decorate this to `Indicator.update_single` if
    you want to force `self.indicator = None` when
    any pre-requisite indicator have `None` value.
    """

    def inner_method(self: AI) -> None:
        if None in self.generate_pre_requisite_values():
            self.indicator = None
        else:
            method(self)

    return inner_method


class RawSeriesIndicator(AbstractIndicator[T]):
    """
    Represents an indicator which is updated by raw value stream.
    """

    def __init__(self, *, raw_values: Iterable[T], **kwargs) -> None:
        super().__init__(default_value=None, **kwargs)
        self._raw_values: Iterator[T] = iter(raw_values)

    def update_single(self) -> None:
        self.indicator = next(self._raw_values)


class ConstantIndicator(AbstractIndicator[T]):
    """
    Represents an constant indicator.
    """

    def __init__(self, constant: T) -> None:
        super().__init__(default_value=constant)

    def update_single(self) -> None:
        pass


class SummationIndicator(AbstractIndicator[T]):
    """
    Summation of indicators.
    """

    def __init__(
        self, *indicators: AbstractIndicator[T], default_value=0, **kwargs
    ) -> None:
        super().__init__(*indicators, default_value=default_value, **kwargs)

    @none_if_none_in_pre_requisites
    def update_single(self) -> None:
        self.indicator = sum(
            self.generate_pre_requisite_values(), start=self._default_value
        )


class MultiplicationIndicator(AbstractIndicator[T]):
    """
    Multiplication of indicators.
    """

    def __init__(
        self, *indicators: AbstractIndicator[T], default_value=1, **kwargs
    ) -> None:
        super().__init__(*indicators, default_value=default_value, **kwargs)

    @none_if_none_in_pre_requisites
    def update_single(self) -> None:
        self.indicator = self._default_value
        for value in self.generate_pre_requisite_values():
            self.indicator *= value  # type: ignore


class SubtractionIndicator(AbstractIndicator[T]):
    """
    Arithmetic subtraction of two indicators.
    """

    def __init__(
        self, indicator1: AbstractIndicator, indicator2: AbstractIndicator
    ) -> None:
        super().__init__(indicator1, indicator2, default_value=None)

    @none_if_none_in_pre_requisites
    def update_single(self) -> None:
        gen = self.generate_pre_requisite_values()
        value1 = next(gen)
        value2 = next(gen)
        self.indicator = value1 - value2  # type: ignore


class DivisionIndicator(AbstractIndicator[T]):
    """
    Arithmetic division of two indicators.
    """

    def __init__(
        self, indicator1: AbstractIndicator, indicator2: AbstractIndicator
    ) -> None:
        super().__init__(indicator1, indicator2, default_value=None)

    @none_if_none_in_pre_requisites
    def update_single(self) -> None:
        gen = self.generate_pre_requisite_values()
        value1 = next(gen)
        value2 = next(gen)
        self.indicator = None if not value2 else value1 / value2


class IndexAccessIndicator(AbstractIndicator[T]):
    """
    Index accessing indicators.
    """

    def __init__(
        self, indicator: AbstractIndicator, index: Any, *args, **kwargs
    ) -> None:
        super().__init__(indicator, **kwargs)
        self._index = index

    @none_if_none_in_pre_requisites
    def update_single(self) -> None:
        value = next(self.generate_pre_requisite_values())
        self.indicator = value[self._index]  # type: ignore
