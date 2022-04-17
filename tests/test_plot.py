import unittest
from unittest.mock import Mock, patch

from src.indicator_management import DataAnimator
from src.indicator_management.errors import IndicatorManagementError
from src.indicator_management.indicators import RawSeriesIndicator


def do_nothing(*args, **kwargs) -> None:
    pass


class PlottingTest(unittest.TestCase):
    @patch("matplotlib.animation.FuncAnimation", Mock(wraps=do_nothing))
    @patch("matplotlib.pyplot.show", Mock(return_value=None))
    def test_plotting(self):
        indicator_raw = RawSeriesIndicator(raw_values=range(100))
        indicator_double = indicator_raw * 2
        indicator_triple = indicator_raw * 3
        indicator_square = indicator_raw**2

        animator = DataAnimator()
        with self.assertRaises(ValueError):
            animator.set_common_xaxis(indicator_raw)
        animator.set_common_xaxis(indicator_raw, "x")
        with self.assertRaises(ValueError):
            animator.set_common_xaxis(indicator_raw, "another_name")
        with self.assertRaises(ValueError):
            animator.set_common_xaxis(name="x")

        with self.assertRaises(IndicatorManagementError):
            animator.show()
        animator.add_yaxes(double=indicator_double, triple=indicator_triple)
        animator.add_yaxes(square=indicator_square)
        animator.show(blit=True)

    @patch("matplotlib.animation.FuncAnimation", Mock(wraps=do_nothing))
    @patch("matplotlib.pyplot.show", Mock(return_value=None))
    def test_update(self):
        indicator_raw = RawSeriesIndicator(raw_values=range(100))
        indicator_double = indicator_raw * 2
        indicator_triple = indicator_raw * 3
        indicator_square = indicator_raw**2

        animator = DataAnimator()
        animator.set_common_xaxis(indicator_raw, "x")
        animator.add_yaxes(double=indicator_double, triple=indicator_triple)
        animator.add_yaxes(square=indicator_square)
        animator._prepare_axes_and_lines(False)
        animator.update({"x": 1, "double": 2, "triple": 3, "square": 1})


if __name__ == "__main__":
    unittest.main()
