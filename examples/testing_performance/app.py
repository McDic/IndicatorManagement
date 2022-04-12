import cProfile
import os
import pstats
from random import random

from indicator_management import (
    RawSeriesIndicator,
    generate_sync,
    multiplication,
    summation,
)


def main(count: int = 10**5, safe_none: bool = True):
    def generate_forever():
        while True:
            yield random()

    raw_series = RawSeriesIndicator(raw_values=generate_forever())
    double_x_plus_1 = summation(
        multiplication(raw_series, 2, start=1, safe_none=safe_none),
        1,
        start=0,
        safe_none=safe_none,
    )

    generate = generate_sync(i=double_x_plus_1)
    for _ in range(count):
        next(generate)


if __name__ == "__main__":
    cProfile.run("main(safe_none=True)", "safe_none_yes.perf")
    cProfile.run("main(safe_none=False)", "safe_none_no.perf")
    p_yes = pstats.Stats("safe_none_yes.perf")
    p_no = pstats.Stats("safe_none_no.perf")
    p_yes.strip_dirs().sort_stats("tottime").print_stats(20)
    p_no.strip_dirs().sort_stats("tottime").print_stats(20)
    os.remove("safe_none_yes.perf")
    os.remove("safe_none_no.perf")
