from ._types import Numeric


class AbstractIsolatedPosition:
    """
    Represents isolated position.
    """

    __slots__ = ("entry_price", "amount")

    def __init__(self, entry_price: Numeric, amount: Numeric) -> None:
        self.entry_price: Numeric = entry_price
        self.amount: Numeric = amount

    def pnl(self, exit_price: Numeric) -> Numeric:
        """
        Calculate PNL based on given `exit_price`.
        You can override this method to perform specific PNL calculation.
        """
        return self.amount * (exit_price - self.entry_price)
