import unittest
from typing import Iterable

from src.indicator_management import (
    RawSeriesIndicator,
    SimpleMovingAverage,
    SummationIndicator,
    generate_sync,
)


class IndicatorTestCase(unittest.TestCase):
    """
    Set of indicator tests.
    """

    @staticmethod
    def create_new_raw_series_and_indicator(
        iterable: Iterable,
    ) -> tuple[list, RawSeriesIndicator]:
        iterable_list = list(iterable)
        return iterable_list, RawSeriesIndicator(raw_values=iterable_list)

    def test_raw_series(self) -> None:
        elements, raw_indicator = self.create_new_raw_series_and_indicator(
            range(-10, 11)
        )

        i1 = raw_indicator * 2
        i2 = raw_indicator - 5
        i3 = i1 * i2
        i4 = -raw_indicator
        i5 = 1 / i4
        i6 = SummationIndicator(i1, i2, i3, i4)
        i7 = i3**0.5
        generator = generate_sync(i1=i1, i2=i2, i3=i3, i4=i4, i5=i5, i6=i6, i7=i7)

        for element in elements:
            generated = next(generator)
            self.assertEqual(element * 2, generated["i1"])
            self.assertEqual(element - 5, generated["i2"])
            self.assertEqual(element * 2 * (element - 5), generated["i3"])
            self.assertEqual(-element, generated["i4"])
            self.assertAlmostEqual(-1 / element if element else None, generated["i5"])
            self.assertEqual(element * 2 * (element - 4) - 5, generated["i6"])
            self.assertAlmostEqual(
                (element * 2 * (element - 5)) ** 0.5, generated["i7"]
            )

    def test_simple_moving_average(self) -> None:
        _, raw_indicator = self.create_new_raw_series_and_indicator(
            [2, 3, 5, 8, 13, None, 21]
        )
        sma3 = SimpleMovingAverage(raw_indicator, 3)
        sma3_values = (obj["sma3"] for obj in generate_sync(sma3=sma3))

        self.assertAlmostEqual(next(sma3_values), 2)
        self.assertAlmostEqual(next(sma3_values), 2.5)
        self.assertAlmostEqual(next(sma3_values), 10 / 3)
        self.assertAlmostEqual(next(sma3_values), 16 / 3)
        self.assertAlmostEqual(next(sma3_values), 26 / 3)
        self.assertAlmostEqual(next(sma3_values), 21 / 2)
        self.assertAlmostEqual(next(sma3_values), 17)


if __name__ == "__main__":
    unittest.main()
