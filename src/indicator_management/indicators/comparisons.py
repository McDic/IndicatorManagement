from typing import cast

from .base import AbstractNumericOperationIndicator, N_or_AIN
from .extra_types import NumericOperationProtocol


class SimpleMin(AbstractNumericOperationIndicator):
    """
    Minimum indicator. Generates minimum of all dependencies'.
    """

    def __init__(self, *pre_requisites: N_or_AIN, **kwargs) -> None:
        super().__init__(
            *pre_requisites,
            numeric_func=cast(NumericOperationProtocol, min),
            **kwargs,
        )


class SimpleMax(AbstractNumericOperationIndicator):
    """
    Maximum indicator. Generates maximum of all dependencies'.
    """

    def __init__(self, *pre_requisites: N_or_AIN, **kwargs) -> None:
        super().__init__(
            *pre_requisites,
            numeric_func=cast(NumericOperationProtocol, max),
            **kwargs,
        )
