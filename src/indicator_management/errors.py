class IndicatorManagementError(Exception):
    """
    Abstract class of all errors in `indicator_management`.
    """


class CannotResolveIndicatorGraph(IndicatorManagementError):
    """
    Raised when the indicator dependencies
    graph cannot be resolved.
    """
