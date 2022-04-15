"""
Simple plot application using `indicator_management`.

This example generates `y = 2x + 50` from
every random integer `x` generated from 1 to 100.

To install matplotlib, type `pip install matplotlib` on terminal.
"""

import random

import matplotlib.pyplot as plt

from indicator_management import generate_sync
from indicator_management.indicators import AbstractIndicator, RawSeriesIndicator


def main():

    i1: AbstractIndicator = RawSeriesIndicator(
        raw_values=(random.randint(1, 100) for _ in range(25))
    )
    i2 = i1 * 2 + 50

    y_total = list(generate_sync(x=i1, y=i2))
    x = [obj["x"] for obj in y_total]
    y = [obj["y"] for obj in y_total]

    fig, ax = plt.subplots(1, 1)
    ax.scatter(x, y)

    w, h = fig.get_size_inches()
    fig.set_size_inches(w * 4, h * 2)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
