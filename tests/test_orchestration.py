import random
import unittest

from src.indicator_management import generate_async, generate_sync
from src.indicator_management.errors import CannotResolveIndicatorGraph
from src.indicator_management.indicators import (
    AbstractIndicator,
    AsyncRawSeriesIndicator,
)


async def random_forever():
    while True:
        yield random.random()


class SyncOrchestrationTest(unittest.TestCase):
    def test_cyclic_dependencies(self):
        x1 = AbstractIndicator()
        x2 = AbstractIndicator(x1)
        x1.lazily_update_pre_requisites(x2)
        with self.assertRaises(CannotResolveIndicatorGraph):
            list(generate_sync(x1=x1, x2=x2))


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
