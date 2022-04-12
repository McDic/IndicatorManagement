from math import cos as _cos
from math import log as _log
from math import sin as _sin
from math import tan as _tan

from .._types import Numeric
from .base import AbstractIndicator, OperationIndicator, indicatorized_arguments


@indicatorized_arguments
def sin(indicator: AbstractIndicator[Numeric], **kwargs) -> OperationIndicator:
    """
    Sine of indicator.
    """
    return OperationIndicator(indicator, operation=_sin, **kwargs)


@indicatorized_arguments
def cos(indicator: AbstractIndicator[Numeric], **kwargs) -> OperationIndicator:
    """
    Cosine of indicator.
    """
    return OperationIndicator(indicator, operation=_cos, **kwargs)


@indicatorized_arguments
def tan(indicator: AbstractIndicator[Numeric], **kwargs) -> OperationIndicator:
    """
    Tangent of indicator.
    """
    return OperationIndicator(indicator, operation=_tan, **kwargs)


@indicatorized_arguments
def log(
    indicator_up: AbstractIndicator[Numeric],
    indicator_base: AbstractIndicator[Numeric],
    **kwargs
) -> OperationIndicator:
    """
    Logarithm of indicator.
    """
    return OperationIndicator(indicator_up, indicator_base, operation=_log, **kwargs)
