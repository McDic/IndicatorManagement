from .base import AbstractIndicator, OperationIndicator, indicatorized_arguments


@indicatorized_arguments
def minimum(*indicators: AbstractIndicator, **kwargs) -> OperationIndicator:
    """
    Minimum indicator. Generates minimum of all dependencies'.
    """
    return OperationIndicator(*indicators, operation=min, **kwargs)


@indicatorized_arguments
def maximum(*indicators: AbstractIndicator, **kwargs) -> OperationIndicator:
    """
    Maximum indicator. Generates maximum of all dependencies'.
    """
    return OperationIndicator(*indicators, operation=max, **kwargs)
