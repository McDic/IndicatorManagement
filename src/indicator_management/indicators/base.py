from __future__ import annotations

from collections import deque
from functools import wraps
from numbers import Number
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterable,
    Callable,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
)

from .._types import BoundMethod, ComparisonFunc, Numeric, T
from ..errors import IndicatorManagementError
from ..settings import get_default_safe_none
from ..utils import (
    chained_keyword_and,
    chained_keyword_or,
    wrapped_chained_comparison,
    wrapped_chained_general_operation,
    wrapped_multiplication,
    wrapped_summation,
)

IOPR_co = TypeVar("IOPR_co", covariant=True)


class IndicatorOperationProtocol(Protocol[IOPR_co]):
    def __call__(
        self, *indicator_or_numbers: Union[AbstractIndicator, Numeric], **kwargs
    ) -> IOPR_co:
        raise NotImplementedError


def indicatorized_arguments(func: Callable[..., T]) -> IndicatorOperationProtocol[T]:
    """
    Convert a function which accepts indicators or numbers.
    In resulting function, all number arguments
    will be changed into `ConstantIndicator`.
    """

    @wraps(func)
    def inner_function(
        *indicator_or_numbers: Union[AbstractIndicator, Numeric], **kwargs
    ) -> T:
        result = []
        for obj in indicator_or_numbers:
            if isinstance(obj, AbstractIndicator):
                result.append(obj)
            elif isinstance(obj, Number):
                result.append(ConstantIndicator(obj))
            else:
                raise TypeError
        return func(*result, **kwargs)

    return inner_function


class AbstractIndicator(Generic[T]):
    """
    Abstract class of all indicators.
    """

    global_nonce: int = 0
    __is_sync__: bool = True

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

    def __add__(self, other) -> OperationIndicator:
        return summation(self, other, start=0)

    def __radd__(self, other) -> OperationIndicator:
        return summation(other, self, start=0)

    def __sub__(self, other) -> OperationIndicator:
        return subtraction(self, other)

    def __rsub__(self, other) -> OperationIndicator:
        return subtraction(other, self)

    def __mul__(self, other) -> OperationIndicator:
        return multiplication(self, other, start=1)

    def __rmul__(self, other) -> OperationIndicator:
        return multiplication(other, self, start=1)

    def __truediv__(self, other) -> OperationIndicator:
        return division(self, other)

    def __rtruediv__(self, other) -> OperationIndicator:
        return division(other, self)

    def __pos__(self) -> AbstractIndicator:
        return self

    def __neg__(self) -> OperationIndicator:
        return self * -1

    def __pow__(self, other) -> OperationIndicator:
        return power(self, other)

    def __rpow__(self, other) -> OperationIndicator:
        return power(other, self)

    # =================================================================================
    # Comparison operations

    def __lt__(self, other) -> OperationIndicator[bool]:
        return less(self, other)

    def __le__(self, other) -> OperationIndicator[bool]:
        return less_or_equal(self, other)

    def __gt__(self, other) -> OperationIndicator[bool]:
        return greater(self, other)

    def __ge__(self, other) -> OperationIndicator[bool]:
        return greater_or_equal(self, other)

    # =================================================================================
    # Logical operations

    def __and__(self, other) -> OperationIndicator:
        return and_operator(self, other, safe_none=False)

    def __or__(self, other) -> OperationIndicator:
        return or_operator(self, other, safe_none=False)

    def __xor__(self, other) -> OperationIndicator:
        return xor_operator(self, other, safe_none=False)

    # =================================================================================
    # Other operations which produces indicators

    def __getitem__(self, index: Any) -> OperationIndicator:
        return index_access(self, index=index)

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
        if self.__is_sync__:
            raise IndicatorManagementError(
                "update_single_async should not be called from sync indicator"
            )
        else:
            raise NotImplementedError

    def update_single(self) -> None:
        """
        Calculate and update new indicator value based on given `sources`.
        """
        if self.__is_sync__:
            raise NotImplementedError
        else:
            raise IndicatorManagementError(
                "update_single should not be called from async indicator"
            )


AI = TypeVar("AI", bound=AbstractIndicator)


def default_if_none_in_pre_requisites(
    method: BoundMethod[AI, None]
) -> Callable[[], None]:
    """
    Decorate this to `Indicator.update_single` if
    you want to force `self.set_value(self._default_value)`
    when any pre-requisite indicator have `None` value.
    """

    def inner_method() -> None:
        self = method.__self__
        if any((indicator(0) is None) for indicator in self.pre_requisites):
            self.set_value(self._default_value)
        else:
            method()

    return inner_method


class RawSeriesIndicator(AbstractIndicator[T]):
    """
    Represents an indicator which is updated by
    synchronous raw value stream.
    """

    def __init__(self, *, raw_values: Iterable[Optional[T]], **kwargs) -> None:
        super().__init__(default_value=None, **kwargs)
        self._raw_values: Iterator[Optional[T]] = iter(raw_values)

    def update_single(self) -> None:
        self.set_value(next(self._raw_values))


class AsyncRawSeriesIndicator(AbstractIndicator[T]):
    """
    Represents an indicator which is updated by
    asynchronous raw value stream.
    """

    __is_sync__: bool = False

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
        super().__init__(default_value=constant, history_length=0)

    def update_single(self) -> None:
        pass

    def __call__(self, index: int) -> Optional[T]:
        return self._default_value


N_or_AIN = Union[Numeric, AbstractIndicator[Numeric]]


class OperationIndicator(AbstractIndicator[T]):
    """
    Base of all operational indicators.
    """

    def __init__(
        self,
        *pre_requisites: AbstractIndicator,
        operation: Callable[..., Optional[T]],
        safe_none: Optional[bool] = None,
        **kwargs,
    ) -> None:
        super().__init__(*pre_requisites, **kwargs)
        self._operation = operation
        if safe_none is None:
            safe_none = get_default_safe_none()
        if safe_none:
            diniprs = default_if_none_in_pre_requisites
            self.update_single = diniprs(self.update_single)  # type: ignore

    def update_single(self) -> None:
        self.set_value(
            self._operation(
                *(pre_requisite(0) for pre_requisite in self.pre_requisites)
            )
        )


@indicatorized_arguments
def summation(
    *indicators: AbstractIndicator, start: T, **kwargs
) -> OperationIndicator[T]:
    """
    Summation of indicators.
    """
    return OperationIndicator(
        *indicators,
        operation=wrapped_summation(start),
        **kwargs,
    )


@indicatorized_arguments
def multiplication(
    *indicators: AbstractIndicator, start: T, **kwargs
) -> OperationIndicator[T]:
    """
    Multiplication of indicators.
    """
    return OperationIndicator(
        *indicators, operation=wrapped_multiplication(start), **kwargs
    )


@indicatorized_arguments
def subtraction(
    indicator1: AbstractIndicator, indicator2: AbstractIndicator, **kwargs
) -> OperationIndicator:
    """
    Subtraction of two indicators.
    """
    return OperationIndicator(
        indicator1, indicator2, operation=(lambda x, y: x - y), **kwargs
    )


@indicatorized_arguments
def division(
    indicator1: AbstractIndicator, indicator2: AbstractIndicator, **kwargs
) -> OperationIndicator:
    """
    Division of two indicators.
    """
    default_value = kwargs.get("default_value")
    return OperationIndicator(
        indicator1,
        indicator2,
        operation=(lambda x, y: x / y if y else default_value),
        **kwargs,
    )


@indicatorized_arguments
def power(
    indicator1: AbstractIndicator, indicator2: AbstractIndicator, **kwargs
) -> OperationIndicator:
    """
    Power operation of two indicators.
    """
    return OperationIndicator(
        indicator1, indicator2, operation=(lambda x, y: x**y), **kwargs
    )


@indicatorized_arguments
def less(*indicators: AbstractIndicator, **kwargs) -> OperationIndicator[bool]:
    """
    Generates `indicators[0] < indicators[1] < ... < indicators[-1]`.
    """
    return OperationIndicator(
        *indicators,
        operation=wrapped_chained_comparison(cast(ComparisonFunc, lambda x, y: x < y)),
        **kwargs,
    )


@indicatorized_arguments
def less_or_equal(*indicators: AbstractIndicator, **kwargs) -> OperationIndicator[bool]:
    """
    Generates `indicators[0] <= indicators[1] <= ... <= indicators[-1]`.
    """
    return OperationIndicator(
        *indicators,
        operation=wrapped_chained_comparison(cast(ComparisonFunc, lambda x, y: x <= y)),
        **kwargs,
    )


@indicatorized_arguments
def greater(*indicators: AbstractIndicator, **kwargs) -> OperationIndicator[bool]:
    """
    Generates `indicators[0] > indicators[1] > ... > indicators[-1]`.
    """
    return OperationIndicator(
        *indicators,
        operation=wrapped_chained_comparison(cast(ComparisonFunc, lambda x, y: x > y)),
        **kwargs,
    )


@indicatorized_arguments
def greater_or_equal(
    *indicators: AbstractIndicator, **kwargs
) -> OperationIndicator[bool]:
    """
    Generates `indicators[0] >= indicators[1] >= ... >= indicators[-1]`.
    """
    return OperationIndicator(
        *indicators,
        operation=wrapped_chained_comparison(cast(ComparisonFunc, lambda x, y: x >= y)),
        **kwargs,
    )


@indicatorized_arguments
def and_keyword(*indicators, **kwargs) -> OperationIndicator[bool]:
    """
    Generates `indicators[0] and indicators[1] and ... and indicators[-1]`.
    """
    return OperationIndicator(*indicators, operation=chained_keyword_and, **kwargs)


@indicatorized_arguments
def or_keyword(*indicators, **kwargs) -> OperationIndicator[bool]:
    """
    Generates `indicators[0] or indicators[1] or ... or indicators[-1]`.
    """
    return OperationIndicator(*indicators, operation=chained_keyword_or, **kwargs)


@indicatorized_arguments
def and_operator(*indicators, **kwargs) -> OperationIndicator:
    """
    Generates `indicators[0] & indicators[1] & ... & indicators[-1]`.
    """
    return OperationIndicator(
        *indicators,
        operation=wrapped_chained_general_operation(lambda x, y: x & y),
        **kwargs,
    )


@indicatorized_arguments
def or_operator(*indicators, **kwargs) -> OperationIndicator:
    """
    Generates `indicators[0] | indicators[1] | ... | indicators[-1]`.
    """
    return OperationIndicator(
        *indicators,
        operation=wrapped_chained_general_operation(lambda x, y: x | y),
        **kwargs,
    )


@indicatorized_arguments
def xor_operator(*indicators, **kwargs) -> OperationIndicator:
    """
    Generaters `indicators[0] ^ indicators[1] ^ ... ^ indicators[-1]`. (xor operator)
    """
    return OperationIndicator(
        *indicators,
        operation=wrapped_chained_general_operation(lambda x, y: x ^ y),
        **kwargs,
    )


def booleanize(indicator: AbstractIndicator, **kwargs) -> OperationIndicator:
    """
    Generates `bool(indicator)`.
    """
    return OperationIndicator(indicator, operation=(lambda x: bool(x)), **kwargs)


def index_access(
    indicator: AbstractIndicator, *, index: Any, **kwargs
) -> OperationIndicator:
    """
    Index access operation of an indicator.
    """
    return OperationIndicator(
        indicator, operation=(lambda x: x[index] if x is not None else None), **kwargs
    )


class AbstractHistoryTrackingIndicator(AbstractIndicator[T]):
    """
    Abstract base of all history-tracking indicators.
    """

    def __init__(
        self, *indicators: AbstractIndicator, tracking_lengths: Iterable[int], **kwargs
    ) -> None:
        super().__init__(*indicators, **kwargs)

        self._tracking_lengths: tuple[int, ...] = tuple(tracking_lengths)
        for indicator, length in zip(indicators, self._tracking_lengths, strict=True):
            if length <= 0:
                raise ValueError("Non-positive length %d given" % (length,))
            indicator.resize_history(length + 1, increase_only=True)

    def remove_tail(self) -> None:
        """
        Perform action related to removal of old values.
        """
        raise NotImplementedError

    def add_head(self) -> None:
        """
        Perform action related to addition of new values.
        """
        raise NotImplementedError

    def update_single(self) -> None:
        self.remove_tail()
        self.add_head()
