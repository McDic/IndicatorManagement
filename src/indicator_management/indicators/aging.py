from .base import AbstractIndicator


class AgingIndicator(AbstractIndicator[int]):
    """
    Aging indicator. If dependency of this indicator's boolean conversion
    is True, then increase the age. Otherwise, set the age to zero.
    """

    def __init__(self, indicator: AbstractIndicator, **kwargs) -> None:
        super().__init__(indicator, default_value=0)

    def update_single(self) -> None:
        value = self.pre_requisites[0](0)
        current_age = self(0)
        self.set_value(current_age + 1 if value else 0)  # type: ignore
