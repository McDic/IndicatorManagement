from .errors import CannotResolveIndicatorGraph
from .indicators import AbstractIndicator


def all_pre_requisites(*indicators: AbstractIndicator) -> set[AbstractIndicator]:
    """
    Return set of all pre-requisites (including ancestors) required by given
    indicators. This method does not detect cyclic dependencies.
    """
    visited_indicators: set[AbstractIndicator] = set()

    def dfs(indicator: AbstractIndicator):
        if indicator in visited_indicators:
            return
        visited_indicators.add(indicator)
        for pre_requisite in indicator.pre_requisites:
            dfs(pre_requisite)

    for indicator in indicators:
        dfs(indicator)
    return visited_indicators


def toposort(*indicators: AbstractIndicator) -> list[list[AbstractIndicator]]:
    """
    Return topological sorted list of given indicators and its ancestors.
    You can concurrently update all indicators in same list element in result.
    """
    expanded_indicators = all_pre_requisites(*indicators)
    result: list[list[AbstractIndicator]] = []
    removed: set[AbstractIndicator] = set()

    graph_forward = {
        indicator: {
            next_indicator
            for next_indicator in indicator.get_post_dependencies()
            if next_indicator in expanded_indicators
        }
        for indicator in expanded_indicators
    }
    graph_backward = {
        indicator: set(indicator.pre_requisites) for indicator in expanded_indicators
    }

    result.append([])
    for indicator in expanded_indicators:
        if not graph_backward[indicator]:
            result[0].append(indicator)
            removed.add(indicator)
    if not result[0]:
        raise CannotResolveIndicatorGraph(
            "There is no basis on given indicators. "
            "Perhaps you made an cyclic dependencies?"
        )

    while result[-1]:
        result.append([])
        for indicator in result[-2]:
            for next_indicator in graph_forward[indicator]:
                if next_indicator in removed:
                    continue
                graph_backward[next_indicator].remove(indicator)
                if not graph_backward[next_indicator]:
                    result[-1].append(next_indicator)
                    removed.add(next_indicator)

    if len(removed) != len(expanded_indicators):
        raise CannotResolveIndicatorGraph(
            "There are some remaining unvisited indicators. "
            "Perhaps you made an cyclic dependencies?"
        )

    result.pop()
    return result
