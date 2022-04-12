import cProfile
import os
import pstats
from random import random

from indicator_management import RawSeriesIndicator, generate_sync


def main(count: int = 10**6):
    def generate_forever():
        while True:
            yield random()

    raw_series = RawSeriesIndicator(raw_values=generate_forever())
    double_x_plus_1 = raw_series * 2 + 1

    generate = generate_sync(i=double_x_plus_1)
    for _ in range(count):
        next(generate)


if __name__ == "__main__":
    cProfile.run("main()", "temp.perf")
    p = pstats.Stats("temp.perf")
    p.strip_dirs().sort_stats("tottime").print_stats(100)
    os.remove("temp.perf")
