import unittest

from src.indicator_management.indicators import RawSeriesIndicator, SummationIndicator
from src.indicator_management.orchestrate import generate


class IndicatorTestCase(unittest.TestCase):
    """
    Set of indicator tests.
    """

    @staticmethod
    def create_new_raw_series_and_indicator() -> tuple[list, RawSeriesIndicator]:
        elements = list(range(-10, 11))
        return elements, RawSeriesIndicator(raw_values=elements)

    def test_raw_series(self):
        elements, raw_indicator = self.create_new_raw_series_and_indicator()

        i1 = raw_indicator * 2
        i2 = raw_indicator - 5
        i3 = i1 * i2
        i4 = -raw_indicator
        i5 = 1 / i4
        i6 = SummationIndicator(i1, i2, i3, i4)
        generator = generate(i1=i1, i2=i2, i3=i3, i4=i4, i5=i5, i6=i6)

        for element in elements:
            generated = next(generator)
            self.assertEqual(element * 2, generated["i1"])
            self.assertEqual(element - 5, generated["i2"])
            self.assertEqual(element * 2 * (element - 5), generated["i3"])
            self.assertEqual(-element, generated["i4"])
            self.assertAlmostEqual(-1 / element if element else None, generated["i5"])
            self.assertEqual(element * 2 * (element - 4) - 5, generated["i6"])


if __name__ == "__main__":
    unittest.main()
