import random

import matplotlib.pyplot as plt

from indicator_management.indicators import RawSeriesIndicator
from indicator_management.orchestration import generate


def main():

    i1 = RawSeriesIndicator(raw_values=(random.randint(1, 10) for _ in range(10)))
    i1 *= 2
    i2 = i1 * 2 + 1

    y_total = list(generate(y1=i1, y2=i2))
    y1 = [obj["y1"] for obj in y_total]
    y2 = [obj["y2"] for obj in y_total]

    fig, ax = plt.subplots(1, 1)
    ax.plot(y1, "r", label="y1")
    ax.plot(y2, "g", label="y2")
    ax.legend()

    w, h = fig.get_size_inches()
    fig.set_size_inches(w * 4, h * 2)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
