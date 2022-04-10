from __future__ import annotations

from collections import deque
from numbers import Number
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterable,
    Callable,
    Generic,
    Hashable,
    Iterable,
    Iterator,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
)

from sortedcontainers import SortedList

from ..utils import multiply, summation
from .extra_types import Numeric, NumericOperationProtocol

T = TypeVar("T")
IOPR_co = TypeVar("IOPR_co", covariant=True)


class IndicatorOperationProtocol(Protocol[IOPR_co]):
    def __call__(
        self, *indicator_or_numbers: Union[AbstractIndicator, Numeric]
    ) -> IOPR_co:
        raise NotImplementedError


def indicatorized_arguments(func: Callable[..., T]) -> IndicatorOperationProtocol[T]:
    """
    Convert a function which accepts indicators or numbers.
    In resulting function, all number arguments
    will be changed into `ConstantIndicator`.
    """

    def inner_function(*indicator_or_numbers: Union[AbstractIndicator, Numeric]) -> T:
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

    global_nonce: int = 0

    def __init__(
        self,
        *pre_requisites: AbstractIndicator,
        default_value: Optional[T] = None,
        history_length: int = 1,
    ) -> None:
        self.id = AbstractIndicator.global_nonce
        AbstractIndicator.global_nonce += 1

        self._default_value = default_value
        self.indicator_history: deque[Optional[T]] = deque(
            (None for _ in range(history_length - 1)),
            maxlen=history_length,
        )

        self._post_dependencies: list[AbstractIndicator] = []

        self.pre_requisites: tuple[AbstractIndicator, ...] = pre_requisites
        assert len(self.pre_requisites) == len(set(self.pre_requisites))
        for pre_requisite in self.pre_requisites:
            pre_requisite._post_dependencies.append(self)
        self.set_value(self._default_value)

    # =================================================================================
    # Indicator / History related

    def set_value(self, v: Optional[T]):
        """
        Set the new value of this indicator.
        """
        self.indicator_history.append(v)

    def resize_history(self, history_length: int, increase_only: bool = True):
        """
        Resize indicator history by given `history_length`.
        If `increase_only` is True, then the resulting length will only be increased.
        """
        if not increase_only or history_length > len(self.indicator_history):
            self.indicator_history = deque(
                self.indicator_history,
                maxlen=history_length,
            )
            self.indicator_history.extendleft(
                (None for _ in range(history_length - len(self.indicator_history)))
            )

    def __call__(self, index: int) -> Optional[T]:
        return self.indicator_history[-1 - index]

    # =================================================================================
    # Arithmetic operations

    @indicatorized_arguments
    def __add__(self, other) -> SummationIndicator:
        return SummationIndicator(cast(AbstractIndicator[Numeric], self), other)

    def __radd__(self, other) -> SummationIndicator:
        return self.__add__(other)

    @indicatorized_arguments
    def __sub__(self, other) -> SubtractionIndicator:
        return SubtractionIndicator(cast(AbstractIndicator[Numeric], self), other)

    @indicatorized_arguments
    def __rsub__(self, other) -> SubtractionIndicator:
        return SubtractionIndicator(other, cast(AbstractIndicator[Numeric], self))

    @indicatorized_arguments
    def __mul__(self, other) -> MultiplicationIndicator:
        return MultiplicationIndicator(cast(AbstractIndicator[Numeric], self), other)

    def __rmul__(self, other):
        return self.__mul__(other)

    @indicatorized_arguments
    def __truediv__(self, other) -> DivisionIndicator:
        return DivisionIndicator(cast(AbstractIndicator[Numeric], self), other)

    @indicatorized_arguments
    def __rtruediv__(self, other) -> DivisionIndicator:
        return DivisionIndicator(other, cast(AbstractIndicator[Numeric], self))

    def __pos__(self) -> AbstractIndicator:
        return self

    def __neg__(self) -> MultiplicationIndicator:
        return self * -1

    @indicatorized_arguments
    def __pow__(self, other) -> PowerIndicator:
        return PowerIndicator(cast(AbstractIndicator[Numeric], self), other)

    @indicatorized_arguments
    def __rpow__(self, other) -> PowerIndicator:
        return PowerIndicator(other, cast(AbstractIndicator[Numeric], self))

    # =================================================================================
    # Other operations which produces indicators

    def __getitem__(self, index) -> IndexAccessIndicator:
        return IndexAccessIndicator(self, index)

    # =================================================================================
    # Extra magic methods

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self):
        return "<Indicator id %d :: Type %s :: History %s :: %d dependencies(%s)>" % (
            self.id,
            str(type(self)).split(".")[-1],
            self.indicator_history,
            len(self.pre_requisites),
            ", ".join(str(indicator.id) for indicator in self.pre_requisites),
        )

    # =================================================================================
    # Helper APIs

    def is_basis(self) -> bool:
        """
        Check if this indicator does not require any pre-requisites.
        """
        return not bool(self.pre_requisites)

    def get_post_dependencies(self) -> set[AbstractIndicator]:
        """
        Get set of post dependencies.
        """
        return set(self._post_dependencies)

    # =================================================================================
    # Update APIs

    async def update_single_async(self) -> None:
        """
        Asynchronously update current indicator.
        """
        self.update_single()

    def update_single(self) -> None:
        """
        Calculate and update new indicator value based on given `sources`.
        """
        raise NotImplementedError


AI = TypeVar("AI", bound=AbstractIndicator)


def default_if_none_in_pre_requisites(
    method: Callable[[AI], None]
) -> Callable[[AI], None]:
    """
    Decorate this to `Indicator.update_single` if
    you want to force `self.set_value(self._default_value)`
    when any pre-requisite indicator have `None` value.
    """

    def inner_method(self: AI) -> None:
        if any((indicator(0) is None) for indicator in self.pre_requisites):
            self.set_value(self._default_value)
        else:
            method(self)

    return inner_method


class RawSeriesIndicator(AbstractIndicator[T]):
    """
    Represents an indicator which is updated by
    synchronous raw value stream.
    """

    def __init__(self, *, raw_values: Iterable[Optional[T]], **kwargs) -> None:
        super().__init__(default_value=None, **kwargs)
        self._raw_values: Iterator[Optional[T]] = iter(raw_values)

    async def update_single_async(self) -> None:
        try:
            self.update_single()
        except StopIteration as exc:
            raise StopAsyncIteration(*exc.args).with_traceback(exc.__traceback__)

    def update_single(self) -> None:
        self.set_value(next(self._raw_values))


class AsyncRawSeriesIndicator(AbstractIndicator[T]):
    """
    Represents an indicator which is updated by
    asynchronous raw value stream.
    """

    def __init__(
        self,
        *,
        raw_values: AsyncIterable[Optional[T]],
        **kwargs,
    ) -> None:
        super().__init__(default_value=None, **kwargs)
        self._raw_values: AsyncGenerator[Optional[T], None] = (
            value async for value in raw_values
        )

    async def update_single_async(self) -> None:
        self.set_value(await self._raw_values.__anext__())


class ConstantIndicator(AbstractIndicator[T]):
    """
    Represents an constant indicator.
    """

    def __init__(self, constant: T) -> None:
        super().__init__(default_value=constant)

    def update_single(self) -> None:
        self.set_value(self._default_value)


N_or_AIN = Union[Numeric, AbstractIndicator[Numeric]]


class AbstractNumericOperationIndicator(AbstractIndicator[Numeric]):
    """
    Abstract base of all indicators made by numeric operations.
    """

    def __init__(
        self,
        *pre_requisites: N_or_AIN,
        numeric_func: NumericOperationProtocol,
        **kwargs,
    ) -> None:
        for pre_requisite in pre_requisites:
            if not isinstance(pre_requisite, (Number, AbstractIndicator)):
                raise TypeError
        super().__init__(
            *(
                pre_requisite
                if isinstance(pre_requisite, AbstractIndicator)
                else ConstantIndicator(pre_requisite)
                for pre_requisite in pre_requisites
            ),
            **kwargs,
        )
        self._numeric_func = numeric_func

    @default_if_none_in_pre_requisites
    def update_single(self):
        self.set_value(
            self._numeric_func(
                *(indicator(0) for indicator in self.pre_requisites)  # type: ignore
            )
        )


class SummationIndicator(AbstractNumericOperationIndicator):
    """
    Summation of indicators.
    """

    def __init__(self, *indicators: N_or_AIN, **kwargs) -> None:
        super().__init__(*indicators, numeric_func=summation, **kwargs)


class MultiplicationIndicator(AbstractNumericOperationIndicator):
    """
    Multiplication of indicators.
    """

    def __init__(self, *indicators: N_or_AIN, **kwargs) -> None:
        super().__init__(*indicators, numeric_func=multiply, **kwargs)


class SubtractionIndicator(AbstractNumericOperationIndicator):
    """
    Arithmetic subtraction of two indicators.
    """

    def __init__(self, indicator1: N_or_AIN, indicator2: N_or_AIN, **kwargs) -> None:
        super().__init__(
            indicator1,
            indicator2,
            numeric_func=cast(NumericOperationProtocol, lambda x, y: x - y),
            **kwargs,
        )


class DivisionIndicator(AbstractNumericOperationIndicator):
    """
    Arithmetic division of two indicators.
    Note that division by zero will make this indicator value to default value.
    """

    def __init__(self, indicator1: N_or_AIN, indicator2: N_or_AIN, **kwargs) -> None:
        super().__init__(
            indicator1,
            indicator2,
            numeric_func=cast(
                NumericOperationProtocol, lambda x, y: x / y if y else None
            ),
            **kwargs,
        )


class PowerIndicator(AbstractNumericOperationIndicator):
    """
    Power operation of two indicators.
    """

    def __init__(self, indicator1: N_or_AIN, indicator2: N_or_AIN, **kwargs) -> None:
        super().__init__(
            indicator1,
            indicator2,
            numeric_func=cast(NumericOperationProtocol, pow),
            **kwargs,
        )


class IndexAccessIndicator(AbstractIndicator[T]):
    """
    Index accessing indicators.
    """

    def __init__(
        self,
        indicator: AbstractIndicator,
        index: Hashable,
        **kwargs,
    ) -> None:
        super().__init__(indicator, **kwargs)
        self._index = index

    @default_if_none_in_pre_requisites
    def update_single(self) -> None:
        value = self.pre_requisites[0](0)
        self.set_value(value[self._index])  # type: ignore


class AbstractHistoryTrackingIndicator(AbstractIndicator[T]):
    """
    Abstract base of all history-tracking indicators.
    This indicator also tracks number of `None`s in tracking history.
    """

    def __init__(self, indicator: AbstractIndicator, length: int, **kwargs) -> None:
        self._tracking_length: int = length
        indicator.resize_history(self._tracking_length, increase_only=True)
        super().__init__(indicator, history_length=self._tracking_length, **kwargs)
        self._removed_value: Optional[Any] = indicator(self._tracking_length - 1)
        self._none_count: int = sum(
            1 for i in range(self._tracking_length) if indicator(i) is None
        )

    def update_single(self) -> None:
        self.update_single_before_history_shift()
        if self._removed_value is None:
            self._none_count -= 1
        self._removed_value = self.pre_requisites[0](self._tracking_length - 1)
        if self.pre_requisites[0](0) is None:
            self._none_count += 1
        self.update_single_after_history_shift()

    def update_single_before_history_shift(self) -> None:
        """
        The first phase of `self.update_single`, which exists for update
        before `self._removed_value` is changed. You should focus on
        some destructive action on removing `self._removed_value` for
        this indicator's value state.
        """
        raise NotImplementedError

    def update_single_after_history_shift(self) -> None:
        """
        The last phase of `self.update_single`, which exists for update
        after `self._removed_value` is changed. You should focus on
        some constructive action on adding `self.pre_requisites[0](0)`
        for this indicator's value state.
        """
        raise NotImplementedError


class AbstractStatisticTrackingIndicator(AbstractHistoryTrackingIndicator[T]):
    """
    Abstract base of all statistic-tracking indicators.
    The reason why statistic is saved in child class
    while history is saved in parent class is, otherwise
    statistic is not reliable when the older value exists.
    """

    def __init__(self, indicator: AbstractIndicator, length: int, **kwargs) -> None:
        super().__init__(indicator, length, **kwargs)
        self.indicator_statistics: SortedList[T] = SortedList()

    def update_single_before_history_shift(self) -> None:
        value = self._removed_value
        if value is not None:
            self.indicator_statistics.remove(value)

    def update_single_after_history_shift(self) -> None:
        value = self.pre_requisites[0](0)
        if value is not None:
            self.indicator_statistics.add(value)
