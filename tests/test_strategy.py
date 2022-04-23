import unittest

from src.indicator_management._types import Numeric
from src.indicator_management.indicators import AbstractIndicator, RawSeriesIndicator
from src.indicator_management.indicators.strategy import AbstractStrategy
from src.indicator_management.orchestration import generate_sync


class JohnberUntilAbsThreshold(AbstractIndicator[bool]):
    """
    Johnber until the price reaches absolute threshold.
    """

    def __init__(
        self, *pre_requisites: AbstractIndicator, threshold: Numeric, **kwargs
    ) -> None:
        super().__init__(*pre_requisites, **kwargs)
        assert threshold > 0
        self.threshold = threshold

    def update_single(self) -> None:
        current_price = self.pre_requisites[0](0)
        entry_price = self.pre_requisites[1](0)
        is_long = self.pre_requisites[2](0)

        if entry_price is None:
            self.set_value(None)
        elif current_price is None or is_long is None:
            raise ValueError
        else:
            self.set_value(
                current_price >= entry_price + self.threshold
                if is_long
                else current_price <= entry_price - self.threshold
            )


class StrategyTest(unittest.TestCase):
    def test_strategy(self):
        prices = [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007]
        signals = [1, 0, 0, 0, 1, -1, 0, 0]

        price_indicator = RawSeriesIndicator(raw_values=prices)
        signal_indicator = RawSeriesIndicator(raw_values=signals)

        with self.assertRaises(ValueError):
            AbstractStrategy(price_indicator, ())
        with self.assertRaises(TypeError):
            AbstractStrategy(price_indicator, 1)

        strategy = AbstractStrategy(
            price_indicator,
            signal_indicator,
            aexc_type=JohnberUntilAbsThreshold,
            aexc_kwargs={"threshold": 2},
        )

        gen = generate_sync(
            price=price_indicator, signal=signal_indicator, strategy=strategy
        )
        self.assertEqual(strategy._realized_pnl, 0)
        next(gen)  # signal = 1; Long
        self.assertGreater(strategy._isolated_positions[0].amount, 0)
        next(gen)
        obj = next(gen)  # AEXC activated; Close
        self.assertEqual(strategy._isolated_positions[0].amount, 0)
        self.assertEqual(obj["strategy"]["pnl"], strategy._realized_pnl)
        self.assertGreater(strategy._realized_pnl, 0)
        self.assertEqual(obj["strategy"]["balance"], sum(strategy._balances))
        self.assertAlmostEqual(obj["strategy"]["balance"], 1002 / 1000)
        next(gen)
        next(gen)  # signal = 1; Long
        self.assertGreater(strategy._isolated_positions[0].amount, 0)
        obj = next(gen)  # signal = -1; Should immediately switch to Short
        self.assertAlmostEqual(obj["strategy"]["balance"], 1002 / 1000 * 1005 / 1004)
        next(gen)
        next(gen)
        self.assertLess(strategy._unrealized_pnls[0], 0)


if __name__ == "__main__":
    unittest.main()
