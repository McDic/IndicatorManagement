import asyncio
from typing import Any, AsyncGenerator, Generator

from .graph import toposort
from .indicators import AbstractIndicator


def generate_sync(
    **indicators: AbstractIndicator,
) -> Generator[dict[str, Any], None, None]:
    """
    Synchronously generate all indicators by flow.
    """
    extended_toposorted: list[list[AbstractIndicator]] = toposort(*indicators.values())
    try:
        while True:
            for batched_indicators in extended_toposorted:
                for indicator in batched_indicators:
                    indicator.update_single()
            yield {
                indicator_name: indicator(0)
                for indicator_name, indicator in indicators.items()
            }
    except StopIteration:
        pass


async def generate_async(
    **indicators: AbstractIndicator,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Asynchronously generate all indicators by flow,
    but reduce context switching as possible.
    """
    extended_toposorted: list[list[AbstractIndicator]] = toposort(*indicators.values())
    extended_classified: list[
        tuple[tuple[AbstractIndicator, ...], tuple[AbstractIndicator, ...]]
    ] = []
    for batched_indicators in extended_toposorted:
        indicators_sync = tuple(
            indicator for indicator in batched_indicators if indicator.__is_sync__
        )
        indicators_async = tuple(
            indicator for indicator in batched_indicators if not indicator.__is_sync__
        )
        extended_classified.append((indicators_sync, indicators_async))

    try:
        while True:
            for sync_indicators, async_indicators in extended_classified:

                for indicator in sync_indicators:
                    indicator.update_single()

                if async_indicators:
                    async_done, async_pending = await asyncio.wait(
                        [
                            asyncio.create_task(indicator.update_single_async())
                            for indicator in async_indicators
                        ],
                        return_when=asyncio.FIRST_EXCEPTION,
                    )
                    while async_done:
                        task = async_done.pop()
                        exc = task.exception()
                        if exc:
                            for running_task in async_pending:
                                running_task.cancel()
                            raise exc

            yield {
                indicator_name: indicator(0)
                for indicator_name, indicator in indicators.items()
            }
    except (StopIteration, StopAsyncIteration):
        pass
