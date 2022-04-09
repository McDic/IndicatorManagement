from .base import AbstractHistoryTrackingIndicator, AbstractIndicator, Numeric


class SimpleMovingAverage(AbstractHistoryTrackingIndicator[Numeric]):
    """
    SMA indicator. Exact formula of this indicator is
    `SMA(source, len) = sum(source, len) / (len - none_count)`
    where `None` is treated as zero and
    `none_count` is number of `None`s in tracking history.
    """

    def __init__(self, indicator: AbstractIndicator, length: int) -> None:
        super().__init__(indicator, length, default_value=None)
        self._sum = 0

    def update_single_before_history_shift(self) -> None:
        self._sum -= self._removed_value or 0.0  # type: ignore

    def update_single_after_history_shift(self) -> None:
        self._sum += self.pre_requisites[0](0) or 0.0  # type: ignore
        self.value = (
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

    def __init__(self, indicator: AbstractIndicator, length: int) -> None:
        super().__init__(indicator, length, default_value=None)
        self._sum = 0
        self._square_sum = 0

    def update_single_before_history_shift(self) -> None:
        self._sum -= self._removed_value or 0.0  # type: ignore
        self._square_sum -= (self._removed_value or 0.0) ** 2  # type: ignore

    def update_single_after_history_shift(self) -> None:
        value = self.pre_requisites[0](0) or 0.0
        self._sum += value  # type: ignore
        self._square_sum += value**2  # type: ignore
        length = self._tracking_length - self._none_count
        self.value = (
            self._square_sum / length - (self._sum / length) ** 2
            if length > 0
            else None
        )


def bollinger_band(
    base_indicator: AbstractIndicator[Numeric],
    length: int,
    stdev_multiplier: float = 2.0,
) -> tuple[AbstractIndicator[Numeric], ...]:
    """
    Return upper bound, middle, and lower bound of Bollinger Band.
    """
    assert stdev_multiplier > 0
    moving_average = SimpleMovingAverage(base_indicator, length)
    bandwidth = SimpleMovingVariance(base_indicator, length) ** 0.5 * stdev_multiplier
    return moving_average + bandwidth, moving_average, moving_average - bandwidth
