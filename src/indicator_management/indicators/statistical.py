from sortedcontainers import SortedList

from .._types import Numeric, T
from .base import AbstractHistoryTrackingIndicator, AbstractIndicator


class SimpleMovingAverage(AbstractHistoryTrackingIndicator[Numeric]):
    """
    SMA indicator. Exact formula of this indicator is
    `SMA(source, len) = sum(source, len) / (len - none_count)`
    where `None` is treated as zero and
    `none_count` is number of `None`s in tracking history.
    """

    def __init__(self, indicator: AbstractIndicator, length: int, **kwargs) -> None:
        super().__init__(indicator, tracking_lengths=(length,), **kwargs)
        self._none_count = sum(
            1
            for i in range(self._tracking_lengths[0])
            if self.pre_requisites[0](i) is None
        )
        self._sum = 0

    def remove_tail(self) -> None:
        value_removal = self.pre_requisites[0](self._tracking_lengths[0])
        self._sum -= value_removal or 0  # type: ignore
        if value_removal is None:
            self._none_count -= 1

    def add_head(self) -> None:
        value_new = self.pre_requisites[0](0)
        self._sum += value_new or 0
        if value_new is None:
            self._none_count += 1

    def update_single(self) -> None:
        super().update_single()
        self.set_value(
            self._sum / (self._tracking_lengths[0] - self._none_count)
            if self._tracking_lengths[0] > self._none_count
            else self._default_value
        )


class SimpleMovingVariance(AbstractHistoryTrackingIndicator[Numeric]):
    """
    Variance indicator. Exact formula of this indicator is
    `Var(source, len) = variance(filter(None, source), len - none_count)`.
    If all values in tracking history are `None`, then produces `None`.
    """

    def __init__(self, indicator: AbstractIndicator, length: int, **kwargs) -> None:
        super().__init__(indicator, tracking_lengths=(length,), **kwargs)
        self._none_count = sum(
            1
            for i in range(self._tracking_lengths[0])
            if self.pre_requisites[0](i) is None
        )
        self._sum = 0
        self._square_sum = 0

    def remove_tail(self) -> None:
        value_removal = self.pre_requisites[0](self._tracking_lengths[0])
        self._sum -= value_removal or 0
        self._square_sum -= (value_removal or 0) ** 2
        if value_removal is None:
            self._none_count -= 1

    def add_head(self) -> None:
        value_new = self.pre_requisites[0](0)
        self._sum += value_new or 0
        self._square_sum += (value_new or 0) ** 2
        if value_new is None:
            self._none_count += 1

    def update_single(self) -> None:
        super().update_single()
        length = self._tracking_lengths[0] - self._none_count
        self.set_value(
            self._square_sum / length - (self._sum / length) ** 2
            if length > 0
            else self._default_value
        )


class SimpleHistoricalStats(AbstractHistoryTrackingIndicator[dict[str, Numeric]]):
    """
    Historical statistical indicator. Generates historical
    minimum, maximum, and median of only dependency.
    The reason why statistic is saved in child class
    while history is saved in parent class is, otherwise
    statistic is not reliable when the older value exists.
    """

    def __init__(self, indicator: AbstractIndicator, length: int, **kwargs) -> None:
        super().__init__(indicator, tracking_lengths=(length,), **kwargs)
        self._indicator_statistics: SortedList[T] = SortedList()

    def remove_tail(self) -> None:
        value_removal = self.pre_requisites[0](self._tracking_lengths[0])
        if value_removal is not None:
            self._indicator_statistics.remove(value_removal)

    def add_head(self) -> None:
        value_new = self.pre_requisites[0](0)
        if value_new is not None:
            self._indicator_statistics.add(value_new)

    def _get_median(self) -> Numeric:
        length = len(self._indicator_statistics)
        if length % 2 == 1:
            return self._indicator_statistics[(length - 1) // 2]
        else:
            return (
                self._indicator_statistics[length // 2]
                + self._indicator_statistics[length // 2 - 1]
            ) / 2

    def update_single(self) -> None:
        super().update_single()
        self.set_value(
            {
                "min": self._indicator_statistics[0],
                "max": self._indicator_statistics[-1],
                "median": self._get_median(),
            }
            if self._indicator_statistics
            else self._default_value
        )
