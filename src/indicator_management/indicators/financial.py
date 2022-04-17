from math import inf

from .._types import Numeric
from .base import (
    AbstractIndicator,
    OperationIndicator,
    multiplication,
    power,
    subtraction,
    summation,
)
from .statistical import SimpleMovingAverage, SimpleMovingVariance
from .utils import PrevDifference, simple_filter


def bollinger_band(
    base_indicator: AbstractIndicator[Numeric],
    length: int,
    stdev_multiplier: float = 2.0,
    **kwargs
) -> tuple[AbstractIndicator[Numeric], ...]:
    """
    Return upper bound, middle, and lower bound of Bollinger Band.
    """
    assert stdev_multiplier > 0
    moving_average = SimpleMovingAverage(base_indicator, length, **kwargs)
    bandwidth = multiplication(
        power(SimpleMovingVariance(base_indicator, length, **kwargs), 0.5, **kwargs),
        stdev_multiplier,
        start=1,
        **kwargs,
    )
    return (  # type: ignore
        summation(moving_average, bandwidth, start=0, **kwargs),
        moving_average,
        subtraction(moving_average, bandwidth, **kwargs),
    )


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


def macd(
    indicator: AbstractIndicator[Numeric], short_period: int, long_period: int, **kwargs
) -> OperationIndicator[Numeric]:
    """
    Moving Average Convergence Divergence.
    `MACD(short, long) = SMA(short) - SMA(long)`.
    """
    return subtraction(
        SimpleMovingAverage(indicator, short_period, **kwargs),
        SimpleMovingAverage(indicator, long_period, **kwargs),
        **kwargs,
    )


def ppo(
    indicator: AbstractIndicator[Numeric], short_period: int, long_period: int, **kwargs
) -> OperationIndicator[Numeric]:
    """
    Percent Price Oscillator.
    See [here](https://www.investopedia.com/terms/p/ppo.asp) for details.
    """
    short = SimpleMovingAverage(indicator, short_period, **kwargs)
    long = SimpleMovingAverage(indicator, long_period, **kwargs)
    return OperationIndicator(
        short, long, operation=(lambda s, l: (s - l) / l * 100), **kwargs
    )


def rsi(
    indicator: AbstractIndicator[Numeric], period: int = 14, **kwargs
) -> OperationIndicator[Numeric]:
    """
    Relative Strength Index.
    See [here](https://www.investopedia.com/terms/r/rsi.asp) for details.
    """
    prev_difference = PrevDifference(indicator)
    gain_filter = simple_filter(prev_difference, 0, (lambda pnl: pnl > 0), **kwargs)
    loss_filter = simple_filter(prev_difference, 0, (lambda pnl: pnl < 0), **kwargs)
    gain_ema = ExponentialMovingAverage(gain_filter, 1.0 / period, **kwargs)
    loss_ema = ExponentialMovingAverage(loss_filter, 1.0 / period, **kwargs)
    return OperationIndicator(
        gain_ema,
        loss_ema,
        operation=(lambda x, y: 100 * (1 - 1 / (1 - (x / y if y else -inf)))),
        **kwargs,
    )
