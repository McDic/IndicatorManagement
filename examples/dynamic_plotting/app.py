"""
Dynamic plot application using matplotlib and Binance's Klines data.

This example generates Simple Moving Average of close price data.
Note that this example does not load all data in memory at once.

To install matplotlib, type `pip install matplotlib` on terminal.
"""

from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Generator, Union

import matplotlib.animation as pltanim
import matplotlib.pyplot as plt

from indicator_management.indicators import (
    AbstractIndicator,
    RawSeriesIndicator,
    SimpleHistoricalStats,
    SimpleMax,
    SimpleMin,
    SimpleMovingAverage,
)
from indicator_management.orchestration import generate_sync


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


def main(maxlen: int = 200):

    indicator_raw_value: AbstractIndicator = RawSeriesIndicator(
        raw_values=generate_timestamp_and_price(
            Path(__file__).parent / "BTCUSDT-1m-2021-06-27.csv"
        )
    )
    indicator_timestamp = indicator_raw_value[0]
    indicator_close_price = indicator_raw_value[1]
    indicator_sma20 = SimpleMovingAverage(indicator_close_price, 20)
    indicator_sma60 = SimpleMovingAverage(indicator_close_price, 60)

    indicator_minimum = SimpleHistoricalStats(
        SimpleMin(indicator_close_price, indicator_sma20, indicator_sma60), maxlen
    )["min"]
    indicator_maximum = SimpleHistoricalStats(
        SimpleMax(indicator_close_price, indicator_sma20, indicator_sma60), maxlen
    )["max"]

    fig, ax = plt.subplots(1, 1)
    (line_close,) = ax.plot([], [], "b", label="close")
    (line_sma20,) = ax.plot([], [], "r--", label="sma20")
    (line_sma60,) = ax.plot([], [], "g--", label="sma60")

    generator = generate_sync(
        timestamp=indicator_timestamp,
        close=indicator_close_price,
        sma20=indicator_sma20,
        sma60=indicator_sma60,
        global_min=indicator_minimum,
        global_max=indicator_maximum,
    )

    data_timestamp: deque[datetime] = deque(maxlen=maxlen)
    data_close: deque[float] = deque(maxlen=maxlen)
    data_sma20: deque[float] = deque(maxlen=maxlen)
    data_sma60: deque[float] = deque(maxlen=maxlen)

    def update(value):
        data_timestamp.append(value["timestamp"])
        data_close.append(value["close"])
        data_sma20.append(value["sma20"])
        data_sma60.append(value["sma60"])

        minimum = value["global_min"]
        maximum = value["global_max"]
        ax.set_ylim(minimum, maximum)
        ax.set_xlim(data_timestamp[0], data_timestamp[-1])

        line_close.set_data(data_timestamp, data_close)
        line_sma20.set_data(data_timestamp, data_sma20)
        line_sma60.set_data(data_timestamp, data_sma60)

        fig.autofmt_xdate()
        ax.figure.canvas.draw()
        return line_close, line_sma20, line_sma60

    ax.legend(loc="upper left")
    animation = pltanim.FuncAnimation(
        fig,
        update,
        frames=generator,
        interval=50,
        blit=True,
        repeat=False,
        save_count=300,
    )
    # animation.save(
    #     "example.gif", progress_callback=lambda i, n: print(f"Saving frame {i}/{n}")
    # )
    plt.show()


if __name__ == "__main__":
    main(50)
