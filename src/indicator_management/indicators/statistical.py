from .base import (
    AbstractHistoryTrackingIndicator,
    AbstractIndicator,
    AbstractStatisticTrackingIndicator,
)
from .extra_types import Numeric


class SimpleMovingAverage(AbstractHistoryTrackingIndicator[Numeric]):
    """
    SMA indicator. Exact formula of this indicator is
    `SMA(source, len) = sum(source, len) / (len - none_count)`
    where `None` is treated as zero and
    `none_count` is number of `None`s in tracking history.
    """

    def __init__(self, indicator: AbstractIndicator, length: int, **kwargs) -> None:
        super().__init__(indicator, length, **kwargs)
        self._sum = 0

    def update_single_before_history_shift(self) -> None:
        self._sum -= self._removed_value or 0.0  # type: ignore

    def update_single_after_history_shift(self) -> None:
        self._sum += self.pre_requisites[0](0) or 0.0  # type: ignore
        self.set_value(
            self._sum / (self._tracking_length - self._none_count)
            if self._tracking_length > self._none_count
            else None
        )


class SimpleMovingVariance(AbstractHistoryTrackingIndicator[Numeric]):
    """
    Variance indicator. Exact formula of this indicator is
    `Var(source, len) = variance(filter(None, source), len - none_count)`.
    If all values in tracking history are `None`, then produces `None`.
    """

    def __init__(self, indicator: AbstractIndicator, length: int, **kwargs) -> None:
        super().__init__(indicator, length, **kwargs)
        self._sum = 0
        self._square_sum = 0

    def update_single_before_history_shift(self) -> None:
        value = self._removed_value or 0.0
        self._sum -= value  # type: ignore
        self._square_sum -= value  # type: ignore

    def update_single_after_history_shift(self) -> None:
        value = self.pre_requisites[0](0) or 0.0
        self._sum += value  # type: ignore
        self._square_sum += value**2  # type: ignore
        length = self._tracking_length - self._none_count
        self.set_value(
            self._square_sum / length - (self._sum / length) ** 2
            if length > 0
            else None
        )


class SimpleHistoricalStats(AbstractStatisticTrackingIndicator[dict[str, Numeric]]):
    """
    Historical statistical indicator. Generates historical minimum,
    maximum, and median of only dependency.
    """

    def _get_median(self) -> Numeric:
        length = len(self.indicator_statistics)
        if length % 2 == 1:
            return self.indicator_statistics[(length - 1) // 2]
        else:
            return (
                self.indicator_statistics[length // 2]
                + self.indicator_statistics[length // 2 - 1]
            ) / 2

    def update_single_after_history_shift(self) -> None:
        super().update_single_after_history_shift()
        self.set_value(
            {
                "min": self.indicator_statistics[0],
                "max": self.indicator_statistics[-1],
                "median": self._get_median(),
            }
            if self.indicator_statistics
            else None
        )
