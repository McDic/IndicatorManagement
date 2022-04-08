from .base import AbstractIndicator, AbstractHistoryTrackingIndicator, Numeric


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
