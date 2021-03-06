import statistics
import unittest
from math import cos as raw_cos
from math import sin as raw_sin
from math import tan as raw_tan
from typing import Any, Callable, Iterable, cast

from src.indicator_management import generate_sync
from src.indicator_management.indicators import (
    AgingIndicator,
    ExponentialMovingAverage,
    PrevDifference,
    RawSeriesIndicator,
    SimpleHistoricalStats,
    SimpleMovingAverage,
    SimpleMovingVariance,
    and_keyword,
    booleanize,
    cos,
    greater,
    greater_or_equal,
    less,
    less_or_equal,
    maximum,
    minimum,
    or_keyword,
    simple_filter,
    sin,
    summation,
    tan,
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
        i6 = summation(i1, i2, i3, i4, start=0)
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

    def test_simple_moving_variance(self) -> None:
        _, raw_indicator = self.create_new_raw_series_and_indicator(
            [2, 3, 5, 8, 13, None, 21]
        )
        smv3 = SimpleMovingVariance(raw_indicator, 3)
        smv3_values = (obj["sma3"] for obj in generate_sync(sma3=smv3))

        self.assertAlmostEqual(next(smv3_values), statistics.pvariance([2]))
        self.assertAlmostEqual(next(smv3_values), statistics.pvariance([2, 3]))
        self.assertAlmostEqual(next(smv3_values), statistics.pvariance([2, 3, 5]))
        self.assertAlmostEqual(next(smv3_values), statistics.pvariance([3, 5, 8]))
        self.assertAlmostEqual(next(smv3_values), statistics.pvariance([5, 8, 13]))
        self.assertAlmostEqual(next(smv3_values), statistics.pvariance([8, 13]))
        self.assertAlmostEqual(next(smv3_values), statistics.pvariance([13, 21]))

    def test_trash_indicators(self) -> None:
        raw_values, raw_indicator = self.create_new_raw_series_and_indicator(
            [1, 2, 3, 4, 5]
        )

        i1 = raw_indicator**0.5 - 1
        i2 = raw_indicator + 7
        i3 = i1 * i2
        i3 / 100
        generator = generate_sync(i1=i1, i2=i2, i3=i3)

        for raw_value, obj in zip(raw_values, generator, strict=True):
            self.assertAlmostEqual(raw_value**0.5 - 1, obj["i1"])
            self.assertAlmostEqual(raw_value + 7, obj["i2"])
            self.assertAlmostEqual((raw_value**0.5 - 1) * (raw_value + 7), obj["i3"])

    def test_trigonometric_indicators(self) -> None:
        raw_values, raw_indicator = self.create_new_raw_series_and_indicator(
            [1, 2, 3, 4, 5]
        )

        i_sin = sin(raw_indicator)
        i_cos = cos(raw_indicator)
        i_tan = tan(raw_indicator)
        for raw_value, obj in zip(
            raw_values, generate_sync(s=i_sin, c=i_cos, t=i_tan), strict=True
        ):
            self.assertAlmostEqual(raw_sin(raw_value), obj["s"])
            self.assertAlmostEqual(raw_cos(raw_value), obj["c"])
            self.assertAlmostEqual(raw_tan(raw_value), obj["t"])

    def test_historial_stats(self) -> None:
        raw_values, raw_indicator = self.create_new_raw_series_and_indicator(
            [7, 5, 2, 8, 6, None, 1]
        )

        i_stats = SimpleHistoricalStats(raw_indicator, 3)
        for i, obj in enumerate(generate_sync(stat=i_stats)):
            self.assertEqual(
                min(filter(None, raw_values[max(0, i - 2) : i + 1])), obj["stat"]["min"]
            )
            self.assertEqual(
                max(filter(None, raw_values[max(0, i - 2) : i + 1])), obj["stat"]["max"]
            )
            self.assertAlmostEqual(
                statistics.median(filter(None, raw_values[max(0, i - 2) : i + 1])),
                obj["stat"]["median"],
            )

    def test_simple_min_max(self) -> None:
        raw_values1, raw_indicator1 = self.create_new_raw_series_and_indicator(
            [1, 1, 2, 2, 3, 3]
        )
        raw_values2, raw_indicator2 = self.create_new_raw_series_and_indicator(
            [2, 3, 1, 3, 1, 2]
        )
        raw_values3, raw_indicator3 = self.create_new_raw_series_and_indicator(
            [3, 2, 3, 1, 2, 1]
        )

        min_indicator = minimum(raw_indicator1, raw_indicator2, raw_indicator3)
        max_indicator = maximum(raw_indicator1, raw_indicator2, raw_indicator3)
        for v1, v2, v3, obj in zip(
            raw_values1,
            raw_values2,
            raw_values3,
            generate_sync(min=min_indicator, max=max_indicator),
            strict=True,
        ):
            self.assertEqual(min(v1, v2, v3), obj["min"])
            self.assertEqual(max(v1, v2, v3), obj["max"])

    def test_simple_comparisons(self) -> None:
        raw_values1, raw_indicator1 = self.create_new_raw_series_and_indicator(
            [1, 1, 1, 2, 3]
        )
        raw_values2, raw_indicator2 = self.create_new_raw_series_and_indicator(
            [1, 1, 2, 1, 2]
        )
        raw_values3, raw_indicator3 = self.create_new_raw_series_and_indicator(
            [1, 2, 3, 1, 1]
        )

        indicator_lt = less(raw_indicator1, raw_indicator2, raw_indicator3)
        indicator_le = less_or_equal(raw_indicator1, raw_indicator2, raw_indicator3)
        indicator_gt = greater(raw_indicator1, raw_indicator2, raw_indicator3)
        indicator_ge = greater_or_equal(raw_indicator1, raw_indicator2, raw_indicator3)
        for v1, v2, v3, obj in zip(
            raw_values1,
            raw_values2,
            raw_values3,
            generate_sync(
                lt=indicator_lt, le=indicator_le, gt=indicator_gt, ge=indicator_ge
            ),
        ):
            self.assertEqual(v1 < v2 < v3, obj["lt"])
            self.assertEqual(v1 <= v2 <= v3, obj["le"])
            self.assertEqual(v1 > v2 > v3, obj["gt"])
            self.assertEqual(v1 >= v2 >= v3, obj["ge"])

    def test_keyword_and_or(self):
        raw_values1, raw_indicator1 = self.create_new_raw_series_and_indicator(
            [True, True, False, False]
        )
        raw_values2, raw_indicator2 = self.create_new_raw_series_and_indicator(
            [True, False, True, False]
        )
        indicator_and = and_keyword(raw_indicator1, raw_indicator2)
        indicator_or = or_keyword(raw_indicator1, raw_indicator2)
        for v1, v2, obj in zip(
            raw_values1,
            raw_values2,
            generate_sync(iand=indicator_and, ior=indicator_or),
            strict=True,
        ):
            self.assertEqual(v1 and v2, obj["iand"])
            self.assertEqual(v1 or v2, obj["ior"])

    def test_operator_and_or_xor(self):
        raw_values1, raw_indicator1 = self.create_new_raw_series_and_indicator(
            [1, 1, 1]
        )
        raw_values2, raw_indicator2 = self.create_new_raw_series_and_indicator(
            [0, 1, 2]
        )
        indicator_and = raw_indicator1 & raw_indicator2
        indicator_or = raw_indicator1 | raw_indicator2
        indicator_xor = raw_indicator1 ^ raw_indicator2
        for v1, v2, obj in zip(
            raw_values1,
            raw_values2,
            generate_sync(iand=indicator_and, ior=indicator_or, ixor=indicator_xor),
            strict=True,
        ):
            self.assertEqual(v1 & v2, obj["iand"])
            self.assertEqual(v1 | v2, obj["ior"])
            self.assertAlmostEqual(v1 ^ v2, obj["ixor"])

    def test_booleanize(self):
        raw_values, raw_indicator = self.create_new_raw_series_and_indicator(
            [True, False, None, 1, 0, 0.0, -12.34, "abc", ""]
        )
        booleanized_safe_none = booleanize(raw_indicator, safe_none=True)
        booleanized_unsafe_none = booleanize(raw_indicator, safe_none=False)
        for v, obj in zip(
            raw_values,
            generate_sync(
                bool_safe_none=booleanized_safe_none,
                bool_unsafe_none=booleanized_unsafe_none,
            ),
            strict=True,
        ):
            self.assertEqual(bool(v) if v is not None else None, obj["bool_safe_none"])
            self.assertEqual(bool(v), obj["bool_unsafe_none"])

    def test_aging(self):
        raw_values, raw_indicator = self.create_new_raw_series_and_indicator(
            [1, 0.5, -2, 1.2, 3.4, 7.8, -9.6, 5.1]
        )
        positive_age = AgingIndicator(raw_indicator > 0)
        emulated_age = 0
        for v, obj in zip(raw_values, generate_sync(age=positive_age), strict=True):
            if v > 0:
                emulated_age += 1
            else:
                emulated_age = 0
            self.assertEqual(emulated_age, obj["age"])

    def test_ema(self):
        raw_values, raw_indicator = self.create_new_raw_series_and_indicator(range(10))
        weight: float = 0.5
        ema_indicator = ExponentialMovingAverage(raw_indicator, forward_weight=weight)
        generator = generate_sync(ema=ema_indicator)

        emulated_value = 0
        for i, (raw_value, generated_value) in enumerate(
            zip(raw_values, generator, strict=True)
        ):
            emulated_value = (
                raw_value
                if not i
                else emulated_value * (1 - weight) + raw_value * weight
            )
            self.assertAlmostEqual(emulated_value, generated_value["ema"])

    def test_simple_filter(self):
        raw_values, raw_indicator = self.create_new_raw_series_and_indicator(range(4))
        f = cast(Callable[[Any], bool], lambda x: x % 2 == 0)
        filter_indicator = simple_filter(raw_indicator, False, f, safe_none=False)
        for v, obj in zip(
            raw_values, generate_sync(filter=filter_indicator), strict=True
        ):
            self.assertEqual(v if f(v) else False, obj["filter"])

    def test_prev_difference(self):
        _, raw_indicator = self.create_new_raw_series_and_indicator(
            2**i for i in range(10)
        )
        prev_difference = PrevDifference(raw_indicator)
        for i, obj in enumerate(generate_sync(pd=prev_difference)):
            self.assertEqual(obj["pd"], 2**i - 2 ** (i - 1) if i > 0 else 0)


if __name__ == "__main__":
    unittest.main()
