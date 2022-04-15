from .._types import Numeric
from .base import AbstractIndicator
from .statistical import SimpleMovingAverage, SimpleMovingVariance


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


class ExponentialMovingAverage(AbstractIndicator[Numeric]):
    """
    EMA indicator. Exact formula of this indicator refers to
    [here](https://www.investopedia.com/terms/m/movingaverage.asp).
    """

    def __init__(
        self, indicator: AbstractIndicator, forward_weight: float = 2 / 21, **kwargs
    ) -> None:
        super().__init__(indicator, **kwargs)
        assert 0 < forward_weight < 1
        self._forward_weight = forward_weight

    def update_single(self) -> None:
        value = self.pre_requisites[0](0)
        prev_value = self(0)
        if value is None:
            self.set_value(self._default_value)
        elif prev_value is None:
            self.set_value(value)
        else:
            self.set_value(
                prev_value * (1 - self._forward_weight)  # type: ignore
                + value * self._forward_weight
            )
