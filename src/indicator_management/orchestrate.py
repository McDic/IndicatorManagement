from typing import Generator

from .indicators.abc import AbstractIndicator


def all_basises(*indicators: AbstractIndicator) -> set[AbstractIndicator]:
    """
    Return set of all basises required by given indicators.
    """
    visited_indicators: set[AbstractIndicator] = set()
    result: set[AbstractIndicator] = set()

    def dfs(indicator: AbstractIndicator):
        if indicator in visited_indicators:
            return
        visited_indicators.add(indicator)
        for pre_requisite in indicator.get_pre_requisites():
            dfs(pre_requisite)
        if indicator.is_basis():
            result.add(indicator)

    for indicator in indicators:
        dfs(indicator)
    return result


def generate(**indicators: AbstractIndicator) -> Generator[dict, None, None]:
    """
    Generate all indicators by flow.
    """

    basises: set[AbstractIndicator] = set(
        indicator for indicator in indicators.values() if indicator.is_basis()
    )
    if not basises:
        raise ValueError("There is no basis indicator")
    elif basises != all_basises(*indicators.values()):
        raise ValueError("All basises should be included in keyword arguments")

    try:
        while True:
            for basis in basises:
                basis.update()
            yield {
                indicator_name: indicator.indicator
                for indicator_name, indicator in indicators.items()
            }
    except StopIteration:
        pass
