from typing import Any, Generator

from .indicators import AbstractIndicator


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


def generate(**indicators: AbstractIndicator) -> Generator[dict[str, Any], None, None]:
    """
    Generate all indicators by flow.
    """

    basises: set[AbstractIndicator] = all_basises(*indicators.values())
    if not basises:
        raise ValueError("There is no basis indicator")

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
