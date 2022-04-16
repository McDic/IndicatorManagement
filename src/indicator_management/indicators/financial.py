from math import inf
from typing import cast

from .._types import Numeric
from .base import (
    AbstractIndicator,
    OperationIndicator,
    division,
    multiplication,
    subtraction,
    summation,
)
from .statistical import SimpleMovingAverage, SimpleMovingVariance
from .utils import PrevDifference, simple_filter


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


def macd(
    indicator: AbstractIndicator[Numeric], short_period: int, long_period: int, **kwargs
) -> OperationIndicator[Numeric]:
    """
    MACD indicator. `MACD(short, long) = SMA(short) - SMA(long)`.
    """
    return subtraction(
        SimpleMovingAverage(indicator, short_period),
        SimpleMovingAverage(indicator, long_period),
        **kwargs
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
    return cast(
        OperationIndicator[Numeric],
        multiplication(
            100,
            subtraction(
                1,
                division(
                    1,
                    summation(
                        1,
                        division(gain_ema, loss_ema, default_value=inf, **kwargs),
                        start=0,
                        **kwargs
                    ),
                    **kwargs
                ),
                **kwargs
            ),
            start=1,
            **kwargs
        ),
    )
