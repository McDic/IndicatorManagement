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
    RawSeriesIndicator,
    macd,
    rsi,
)


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
    indicator_macd = macd(indicator_close_price, 20, 60)
    indicator_rsi = rsi(indicator_close_price, period=60)
    indicator_rsi_macd = rsi(indicator_macd, period=60)

    data_animator = DataAnimator(window_length=100)
    data_animator.set_common_xaxis(indicator_timestamp, "timestamp")
    data_animator.add_yaxes(close=indicator_close_price)
    data_animator.add_yaxes(macd=indicator_macd)
    data_animator.add_yaxes(rsi=indicator_rsi, rsi_macd=indicator_rsi_macd)
    data_animator.show(interval=7, blit=False, show_grid=True)


if __name__ == "__main__":
    main()
