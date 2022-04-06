from __future__ import annotations
from typing import Any, Generator, Generic, Iterable, Optional, TypeVar


T = TypeVar("T")


class AbstractIndicator(Generic[T]):
    """
    Abstract class of all indicators.
    """

    def __init__(
        self,
        *,
        default_value: Optional[T] = None,
        pre_requisites: Iterable[AbstractIndicator] = (),
    ) -> None:
        self._default_value = default_value
        self.indicator: Optional[T] = default_value
        self._post_dependencies: list[AbstractIndicator] = []

        pre_requisites = list(pre_requisites)
        self._pre_requisites_trigger: dict[AbstractIndicator, bool] = {
            pre_requisite: False for pre_requisite in pre_requisites
        }
        self._pre_requisites_values: dict[AbstractIndicator, Any] = {
            pre_requisite: pre_requisite.indicator for pre_requisite in pre_requisites
        }
        self._pre_requisite_counter: int = len(pre_requisites)
        for pre_requisite in self._pre_requisites_trigger:
            pre_requisite._post_dependencies.append(self)

    # =================================================================================
    # Helper APIs

    def get_pre_requisites(self) -> Generator[AbstractIndicator, None, None]:
        yield from self._pre_requisites_trigger.keys()

    def is_basis(self) -> bool:
        """
        Check if this indicator does not require any pre-requisites.
        """
        return not bool(self._pre_requisites_trigger)

    # =================================================================================
    # Update APIs

    def trigger_from_pre_requisite(self, pre_requisite: AbstractIndicator) -> None:
        """
        Receive trigger from pre-requisite of this indicator.
        If condition is satisfied, update current indicator.
        If you give any indicator which is not pre-requisite
        of this indicator, it will raise an `KeyError`.
        """
        self._pre_requisites_values[pre_requisite] = pre_requisite.indicator
        if not self._pre_requisites_trigger[pre_requisite]:
            self._pre_requisites_trigger[pre_requisite] = True
            self._pre_requisite_counter -= 1

        if self._pre_requisite_counter == 0:
            self._pre_requisite_counter = len(self._pre_requisites_trigger)
            self._pre_requisites_trigger = {
                pr: False for pr in self._pre_requisites_trigger
            }
            self.update()

    def update(self) -> None:
        """
        Update current indicator and all dependent indicators.
        """
        self.update_single()
        for dependent_indicator in self._post_dependencies:
            dependent_indicator.trigger_from_pre_requisite(self)

    def update_single(self) -> None:
        """
        Calculate and update new indicator value based on given `sources`.
        """
        raise NotImplementedError
