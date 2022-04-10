from .base import AbstractIndicator
from .extra_types import Numeric
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
