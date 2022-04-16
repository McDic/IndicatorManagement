import asyncio
import cProfile
import os
import pstats
from random import random

from indicator_management import generate_async
from indicator_management.indicators import (
    AsyncRawSeriesIndicator,
    multiplication,
    summation,
)


async def main(count: int = 10**5, safe_none: bool = False):
    async def generate_forever():
        while True:
            yield random()

    raw_series = AsyncRawSeriesIndicator(raw_values=generate_forever())
    double_x_plus_1 = summation(
        multiplication(raw_series, 2, start=1, safe_none=safe_none),
        1,
        start=0,
        safe_none=safe_none,
    )

    generate = generate_async(i=double_x_plus_1)
    for _ in range(count):
        await generate.__anext__()


if __name__ == "__main__":
    cProfile.run("asyncio.run(main())", "async_test.perf")
    p = pstats.Stats("async_test.perf")
    p.strip_dirs().sort_stats("tottime").print_stats(20)
    os.remove("async_test.perf")
