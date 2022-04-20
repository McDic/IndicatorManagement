from typing import Any, Generator, Iterable, Optional, Type, cast

from ..._types import Numeric
from ...errors import IndicatorManagementError
from ...position import AbstractIsolatedPosition
from ..base import AbstractIndicator, ConstantIndicator, RawSeriesIndicator
from .exit_conditions import TrailingStop


class AbstractStrategy(AbstractIndicator[dict[str, Any]]):
    """
    Abstract base of all strategies. Strategy is based on given
    condition indicators. When one of given `entry_conditions`
    generates true value, then strategy enters position corresponding
    to that index. And then `exit_plan` calculates the exit condition
    to determine if opened positions should exit or not.

    For `entry_conditions`, generated value should be numeric. Strategy
    will long if it's positive, short if it's negative, holding if
    it's zero, close all if it's None.

    For `indicator_deadline`, the strategy stops all simulations when the
    deadline indicator yields true value. If `None` is given, then runs forever.

    For `aexc_type`, `aexc_args` and `aexc_kwargs`, `aexc` means
    "additional exit condition."
    """

    def __init__(
        self,
        price_indicator: AbstractIndicator[Numeric],
        entry_conditions: tuple[AbstractIndicator, ...],
        *,
        position_type: Type[AbstractIsolatedPosition] = AbstractIsolatedPosition,
        indicator_deadline: Optional[AbstractIndicator] = None,
        aexc_type: Type[AbstractIndicator] = TrailingStop,
        aexc_args: Iterable[AbstractIndicator] = (),
        aexc_kwargs: Optional[dict[str, Any]] = None,
        init_amount: Iterable[Numeric] = (),
        slippage: float = 0.1 * 0.01,
        fee: float = 0.0,
        **kwargs,
    ) -> None:
        if not entry_conditions:
            raise ValueError("Given indicators is empty")
        self._entry_conditions = entry_conditions
        self._deadline = (
            ConstantIndicator(False)
            if indicator_deadline is None
            else indicator_deadline
        )
        self._priceline = price_indicator

        self._isolated_positions: list[AbstractIsolatedPosition] = [
            position_type(entry_price=cast(Numeric, 1), amount=cast(Numeric, 0))
            for _ in range(len(self._entry_conditions))
        ]

        self._balances: list[Numeric] = (
            list(init_amount)
            if init_amount
            else [cast(Numeric, 1.0) for _ in self._entry_conditions]
        )
        if len(self._balances) != len(self._entry_conditions):
            raise ValueError(
                "Length of balances is not same as length of entry conditions"
            )

        self._realized_pnl: Numeric = cast(Numeric, 0.0)
        self._unrealized_pnls: list[Numeric] = [
            cast(Numeric, 0.0) for _ in self._balances
        ]

        aexc_kwargs = aexc_kwargs or {}
        self._aexcs: tuple[AbstractIndicator, ...] = tuple(
            aexc_type(
                self._priceline,
                RawSeriesIndicator(raw_values=self._yield_entry_price(i)),
                RawSeriesIndicator(raw_values=self._yield_is_long(i)),
                *aexc_args,
                **aexc_kwargs,
            )
            for i in range(len(self._isolated_positions))
        )

        super().__init__(
            price_indicator, self._deadline, *entry_conditions, *self._aexcs, **kwargs
        )

        self._slippage: Numeric = cast(Numeric, slippage)
        self._fee: Numeric = cast(Numeric, fee)

    def _yield_entry_price(
        self, index: int
    ) -> Generator[Optional[Numeric], None, None]:
        """
        Yield entry price of `index`-th position forever.
        """
        while True:
            position = self._isolated_positions[index]
            yield position.entry_price if position.amount != 0 else None

    def _yield_is_long(self, index: int) -> Generator[Optional[bool], None, None]:
        """
        Yield `is_long` of `index`-th position forever.
        """
        while True:
            position = self._isolated_positions[index]
            if position.amount == 0:
                yield None
            else:
                yield (position.amount > 0)

    def calculate_fee(self, price: Numeric, amount: Numeric) -> Numeric:
        return self._fee * price * abs(amount)

    def enter_position(
        self,
        index: int,
        is_long: bool,
        *,
        none_silence: bool = False,
        current_price: Optional[Numeric] = None,
    ) -> None:
        """
        Enter position at given `index`, with current price.
        This method should be called inside of `run_atomic`.
        """
        print(
            "Entering position at slot %d (current price %s, %s)"
            % (index, current_price, "long" if is_long else "short")
        )
        position = self._isolated_positions[index]
        if position.amount:
            raise IndicatorManagementError(
                "Tried to open existing position at slot %d" % (index,)
            )

        current_price = current_price or self._priceline(0)
        if current_price is None:
            if none_silence:
                return
            else:
                raise ValueError("Tried to enter position when current price is None")

        position.entry_price = current_price
        position.amount = self._balances[index] / current_price * (1 if is_long else -1)
        this_fee = self.calculate_fee(price=current_price, amount=position.amount)
        self._balances[index] -= this_fee
        print("\tPaid %f fee" % (this_fee,))

    def close_position(
        self,
        index: int,
        none_silence: bool = False,
        current_price: Optional[Numeric] = None,
    ) -> None:
        """
        Close position at given `index`, with current price.
        This method should be called inside of `run_atomic`.
        """
        print("Closing position at slot %d (current price %s)" % (index, current_price))
        position = self._isolated_positions[index]
        if not position.amount:
            raise IndicatorManagementError(
                "Tried to close non-existing position at slot %d" % (index,)
            )

        current_price = current_price or self._priceline(0)
        if current_price is None:
            if none_silence:
                return
            else:
                raise ValueError("Tried to exit position when current price is None")

        this_pnl = position.pnl(current_price)
        this_fee = self.calculate_fee(price=current_price, amount=position.amount)
        self._realized_pnl += this_pnl
        self._balances[index] += this_pnl - this_fee
        print("\tEarned %f, paid %f fee" % (this_pnl, this_fee))
        self._unrealized_pnls[index] = cast(Numeric, 0)
        position.amount = cast(Numeric, 0)

    def run_atomic(self):
        """
        Run atomic cycle. Assumes the entry conditions are already updated.
        """
        current_price = self._priceline(0)
        if current_price is None:
            raise ValueError

        for i, indicator in enumerate(self._entry_conditions):
            position = self._isolated_positions[i]
            signal = indicator(0)
            if signal is None:  # Close all
                if position.amount:
                    print("Closing because signal is none")
                    self.close_position(i, current_price=current_price)
            elif self._aexcs[i](0):  # Additional exit condition activated
                if position.amount:
                    print("Closing because aexc is activated")
                    self.close_position(i, current_price=current_price)
            elif signal == 0:  # Hold
                pass
            elif not position.amount:  # Can enter position
                print("Entering because signal is activated")
                self.enter_position(i, signal > 0, current_price=current_price)
            elif position.amount * signal < 0:  # Inverse signal detected
                print("Closing because signal is opposite")
                self.close_position(i, current_price=current_price)

            self._unrealized_pnls[i] = position.pnl(current_price)

    def update_single(self) -> None:
        self.run_atomic()
        result: dict = {
            "pnl": self._realized_pnl,
            "balance": sum(self._balances),
            "unrealized_pnl": self._realized_pnl + sum(self._unrealized_pnls),
        }
        self.set_value(result)
