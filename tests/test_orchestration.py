import random
import unittest

from src.indicator_management import generate_async
from src.indicator_management.indicators import AsyncRawSeriesIndicator


async def random_forever():
    while True:
        yield random.random()


class AsyncOrchestrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_simple(self):
        x1 = AsyncRawSeriesIndicator(raw_values=random_forever())
        x2 = AsyncRawSeriesIndicator(raw_values=random_forever())
        add = x1 + x2
        async_generator = generate_async(x1=x1, x2=x2, add=add)

        iteration = 0
        while iteration < 10:
            obj = await async_generator.__anext__()
            self.assertAlmostEqual(obj["x1"] + obj["x2"], obj["add"])
            iteration += 1


if __name__ == "__main__":
    unittest.main()
