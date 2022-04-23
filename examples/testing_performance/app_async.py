import asyncio
import cProfile
import os
import pstats
from random import random

from indicator_management import generate_async
from indicator_management.indicators import AsyncRawSeriesIndicator
from indicator_management.log import setup_base_logger_setting
from indicator_management.settings import set_default_safe_none


async def main(count: int = 2 * 10**5, safe_none: bool = False):
    async def generate_forever():
        while True:
            yield random()

    set_default_safe_none(safe_none)
    raw_series = AsyncRawSeriesIndicator(raw_values=generate_forever())
    double_x_plus_1 = 2 * raw_series + 1

    generate = generate_async(i=double_x_plus_1)
    for _ in range(count):
        await generate.__anext__()


if __name__ == "__main__":
    setup_base_logger_setting("log/performance_test_async.log")
    cProfile.run("asyncio.run(main())", "async_test.perf")
    p = pstats.Stats("async_test.perf")
    p.strip_dirs().sort_stats("tottime").print_stats(20)
    os.remove("async_test.perf")
