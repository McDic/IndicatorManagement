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
    """
    return OperationIndicator(
        indicator,
        operation=(lambda x: x if filter_func(x) else false_value),
        default_value=false_value,
        **kwargs
    )


class PrevDifference(AbstractHistoryTrackingIndicator[Numeric]):
    """
    Generates `pre_requisite[0](0) - pre_requisite[0](1)`.
    """

    def __init__(self, indicator: AbstractIndicator, **kwargs) -> None:
        super().__init__(indicator, tracking_lengths=(2,), default_value=0, **kwargs)

    def update_single(self) -> None:
        pre_requisite = self.pre_requisites[0]
        val0, val1 = pre_requisite(0), pre_requisite(1)
        if val0 is not None and val1 is not None:
            self.set_value(val0 - val1)
        else:
            self.set_value(self._default_value)
