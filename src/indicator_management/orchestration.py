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
                indicator_name: indicator.value
                for indicator_name, indicator in indicators.items()
            }
    except StopIteration:
        pass


async def generate_async(
    **indicators: AbstractIndicator,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Asynchronously generate all indicators by flow.
    """
    extended_toposorted: list[list[AbstractIndicator]] = toposort(*indicators.values())
    try:
        while True:
            for batched_indicators in extended_toposorted:
                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(indicator.update_single_async())
                        for indicator in batched_indicators
                    ],
                    return_when=asyncio.FIRST_EXCEPTION,
                )
                while done:
                    task = done.pop()
                    exc = task.exception()
                    if exc:
                        for running_task in pending:
                            running_task.cancel()
                        raise exc
            yield {
                indicator_name: indicator.value
                for indicator_name, indicator in indicators.items()
            }
    except StopAsyncIteration:
        pass
