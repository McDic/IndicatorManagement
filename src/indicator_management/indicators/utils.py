from typing import Any, Callable

from .._types import Numeric
from .base import (
    AbstractHistoryTrackingIndicator,
    AbstractIndicator,
    OperationIndicator,
)


def simple_filter(
    indicator: AbstractIndicator,
    false_value: Any,
    filter_func: Callable[[Any], bool] = bool,
    **kwargs
) -> OperationIndicator:
    """
    Simple filter operation.
    Generates `v if filter_func(v) else false_value`.
    If `filter_func` is None, filter true values.
    """
    return OperationIndicator(
        indicator,
        operation=(lambda x: x if filter_func(x) else false_value),
        default_value=false_value,
    )


class PrevDifference(AbstractHistoryTrackingIndicator[Numeric]):
    """
    Generates `pre_requisite[0](0) - pre_requisite[0](1)`.
    """

    def __init__(self, indicator: AbstractIndicator, **kwargs) -> None:
        super().__init__(indicator, tracking_lengths=(2,), default_value=0, **kwargs)

    def update_single(self) -> None:
        pre_requisite = self.pre_requisites[0]
        self.set_value(pre_requisite(0) - pre_requisite(1))  # type: ignore
