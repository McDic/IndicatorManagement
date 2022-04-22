"""
Dynamic plot application using Binance's Klines data.
Note that this example does not load all data in memory at once.
"""

from datetime import datetime
from pathlib import Path
from typing import Generator, Union

from indicator_management import DataAnimator
from indicator_management.indicators import (
    AbstractIndicator,
    OperationIndicator,
    RawSeriesIndicator,
    rsi,
)
from indicator_management.indicators.strategy import AbstractStrategy


def generate_timestamp_and_price(
    filepath: Union[str, Path]
) -> Generator[tuple[datetime, float], None, None]:
    with open(filepath) as file:
        for line in file:
            if not line:
                break
            splitted = line.split(",")
            timestamp = datetime.fromtimestamp(float(splitted[0]) / 1000)
            close_price = float(splitted[4])
            yield timestamp, close_price


def main():
    indicator_raw_value: AbstractIndicator = RawSeriesIndicator(
        raw_values=generate_timestamp_and_price(
            Path(__file__).parent / "BTCUSDT-1m-2021-06-27.csv"
        )
    )
    indicator_timestamp = indicator_raw_value[0]
    indicator_close_price = indicator_raw_value[1]
    indicator_rsi = rsi(indicator_close_price, period=14)

    def func(x: float) -> int:
        if x >= 75:
            return -1
        elif x <= 25:
            return 1
        else:
            return 0

    condition = OperationIndicator(indicator_rsi, operation=func, safe_none=False)

    strategy = AbstractStrategy(
        indicator_close_price,
        (condition,),
        aexc_kwargs={"bad_ratio": 0.98},
        fee=0.04 * 0.01,
        indicator_timeline=indicator_timestamp,
    )
    unrealized_pnl = strategy["unrealized_pnl"]

    data_animator = DataAnimator(window_length=10**4)
    data_animator.set_common_xaxis(indicator_timestamp, "timestamp")
    data_animator.add_yaxes(close=indicator_close_price)
    data_animator.add_yaxes(rsi=indicator_rsi)
    data_animator.add_yaxes(unrealized_pnl=unrealized_pnl)
    data_animator.show(interval=7, blit=False, show_grid=True)


if __name__ == "__main__":
    main()
