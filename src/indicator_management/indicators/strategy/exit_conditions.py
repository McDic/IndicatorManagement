from math import inf
from typing import Optional, cast

from ..._types import Numeric
from ..base import AbstractIndicator


class TrailingStop(AbstractIndicator[bool]):
    """
    Trailing stop indicator. It has 3 dependencies which yields
    `(Current price, Entry Price, Is Long?)`.
    These 3 dependencies should be specified by lazy update.
    """

    def __init__(
        self,
        *pre_requisites: AbstractIndicator,
        bad_ratio: Numeric = cast(Numeric, 0.98),
        **kwargs
    ) -> None:
        super().__init__(*pre_requisites, **kwargs)
        self.historical_max_price: Numeric = cast(Numeric, -inf)
        self.historical_min_price: Numeric = cast(Numeric, inf)
        self._previous_entry_price: Optional[Numeric] = None
        self._previous_is_long: Optional[bool] = None
        self.bad_ratio: Numeric = bad_ratio

    def reset_values(self):
        """
        Reset all historical values.
        """
        self.historical_max_price = cast(Numeric, -inf)
        self.historical_min_price = cast(Numeric, inf)
        self._previous_entry_price = None
        self._previous_is_long = None

    def update_single(self) -> None:
        current_price = self.pre_requisites[0](0)
        entry_price = self.pre_requisites[1](0)
        is_long = self.pre_requisites[2](0)

        if entry_price is None:
            self.reset_values()
            self.set_value(None)
            return
        elif current_price is None or is_long is None:
            raise ValueError(
                "Current price or is_long is None while entry price is not None"
            )
        elif (
            self._previous_entry_price != entry_price
            or self._previous_is_long != is_long
        ):
            self.historical_max_price = current_price
            self.historical_min_price = current_price
            self._previous_entry_price = entry_price
            self._previous_is_long = is_long

        self.historical_max_price = max(self.historical_max_price, current_price)
        self.historical_min_price = min(self.historical_min_price, current_price)
        if is_long:
            ratio = self.historical_max_price / entry_price
            self.set_value(
                current_price
                <= min(self.bad_ratio * ratio, (ratio + 1) / 2) * entry_price
            )
        else:
            ratio = self.historical_min_price / entry_price
            self.set_value(
                current_price
                >= max(ratio / self.bad_ratio, (ratio + 1) / 2) * entry_price
            )
