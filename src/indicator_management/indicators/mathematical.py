from math import cos, e, log, sin, tan
from typing import cast

from .base import AbstractNumericOperationIndicator, N_or_AIN
from .extra_types import NumericOperationProtocol


class SineIndicator(AbstractNumericOperationIndicator):
    """
    Sine of indicator.
    """

    def __init__(self, indicator: N_or_AIN, **kwargs) -> None:
        super().__init__(
            indicator, numeric_func=cast(NumericOperationProtocol, sin), **kwargs
        )


class CosineIndicator(AbstractNumericOperationIndicator):
    """
    Cosine of indicator.
    """

    def __init__(self, indicator: N_or_AIN, **kwargs) -> None:
        super().__init__(
            indicator, numeric_func=cast(NumericOperationProtocol, cos), **kwargs
        )


class TangentIndicator(AbstractNumericOperationIndicator):
    """
    Tangent of indicator.
    """

    def __init__(self, indicator: N_or_AIN, **kwargs) -> None:
        super().__init__(
            indicator, numeric_func=cast(NumericOperationProtocol, tan), **kwargs
        )


class LogarithmIndicator(AbstractNumericOperationIndicator):
    """
    Logarithm of indicator.
    """

    def __init__(
        self, indicator_x: N_or_AIN, indicator_base: N_or_AIN = e, **kwargs
    ) -> None:
        super().__init__(
            indicator_x,
            indicator_base,
            numeric_func=cast(NumericOperationProtocol, log),
            **kwargs
        )
