import asyncio
import threading
import warnings
from collections import deque
from datetime import datetime
from queue import Empty as EmptyQueueError
from queue import Queue
from typing import Any, AsyncGenerator, Generator, Optional

import matplotlib.animation as pltanim
import matplotlib.pyplot as plt

from .errors import IndicatorManagementError
from .indicators import AbstractIndicator, RawSeriesIndicator
from .orchestration import generate_async, generate_sync
from .utils import range_forever


class DataAnimator:
    """
    Data animator, implemented using `matplotlib`.
    In produced animation, all data share same x-axis.
    This is an experimental feature.
    """

    def __init__(self, window_length: Optional[int] = 200) -> None:
        # Matplotlib settings
        self._figure = plt.figure(figsize=(12, 9))
        self._figure.canvas.manager.set_window_title(
            "IndicatorManagement made by McDic"
        )
        self._window_length = window_length
        self._func_animation: Optional[pltanim.FuncAnimation] = None

        # Indicator registration
        self._names_by_indicator: dict[AbstractIndicator, str] = {}
        self._indicators_by_name: dict[str, AbstractIndicator] = {}
        self._indicator_x_axis: Optional[AbstractIndicator] = None
        self._name_x_axis: str = ""

        # Axes, Plot datas
        self._linedata: dict[str, deque[Any]] = {}
        self._lines: dict[str, list[plt.Line2D]] = {}
        self._axes: list[plt.Axes] = []
        self._axes_nonce: int = 0
        self._names_by_axes_id: list[set[str]] = []

    def _register_indicator(self, indicator: AbstractIndicator, name: str) -> None:
        """
        Register indicator with given name. If there is already same indicator
        but with different name, raises `ValueError`.
        """
        pre_existing_name = self._names_by_indicator.get(indicator)
        if pre_existing_name is not None:
            if pre_existing_name != name:
                raise ValueError(
                    "Name [%s] already exists for given indicator %s"
                    % (name, indicator)
                )
        elif name in self._indicators_by_name:
            raise ValueError("Name [%s] already reserved")
        else:
            self._names_by_indicator[indicator] = name
            self._indicators_by_name[name] = indicator
            self._linedata[name] = deque(maxlen=self._window_length)

    def set_common_xaxis(
        self,
        x_axis_indicator: Optional[AbstractIndicator] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Set common x-axis by given indicator.
        """
        if x_axis_indicator is None:
            x_axis_indicator = RawSeriesIndicator(raw_values=range_forever())

        if self._indicator_x_axis:
            warnings.warn(UserWarning("X axis indicator already exists, overriding.."))

        if name is None:
            name = self._names_by_indicator.get(x_axis_indicator)
        if name is None:
            raise ValueError(
                "X-axis indicator is not registered yet, but no name given"
            )

        self._register_indicator(x_axis_indicator, name)
        self._indicator_x_axis = x_axis_indicator
        self._name_x_axis = name

    def add_yaxes(self, **kwargs: AbstractIndicator) -> None:
        """
        Add y-axes. This method doesn't create `plt.Axes`, because it
        cannot determine how many `plt.Axes` will be created at this moment.
        """
        self._axes_nonce += 1
        self._names_by_axes_id.append(set())
        for name, indicator in kwargs.items():
            self._register_indicator(indicator, name)
            self._names_by_axes_id[-1].add(name)

    def _prepare_axes_and_lines(self, blit: bool, show_grid: bool):
        """
        Prepare `Axes`s and `Line2D`s before showing animation.
        """
        if self._axes_nonce == 0:
            raise IndicatorManagementError(
                "`_axes_nonce` is zero. "
                "Perhaps you called `update` without adding y-axes?"
            )
        assert not self._axes
        self._axes = [self._figure.add_subplot(self._axes_nonce, 1, 1)]
        self._axes.extend(
            self._figure.add_subplot(self._axes_nonce, 1, i + 1, sharex=self._axes[0])
            for i in range(1, self._axes_nonce)
        )

        assert not self._lines
        for i, names in enumerate(self._names_by_axes_id):
            for name in names:
                if name not in self._lines:
                    self._lines[name] = []
                self._lines[name].extend(self._axes[i].plot([], [], label=name))

        for ax in self._axes:
            ax.legend(loc="upper left")
            if blit:
                ax.xaxis.set_animated(True)
                ax.yaxis.set_animated(True)
            if show_grid:
                ax.grid(True, "major", "y")

        self._figure.tight_layout()
        self._figure.subplots_adjust(hspace=0)

    def update(self, value: Optional[dict[str, Any]]) -> list[plt.Artist]:
        """
        Update data and lines.
        """
        if value is None:
            return []

        for name in self._indicators_by_name:
            self._linedata[name].append(value[name])

        for name in self._lines:
            for line in self._lines[name]:
                line.set_data(self._linedata[self._name_x_axis], self._linedata[name])

        self._axes[0].set_xlim(
            self._linedata[self._name_x_axis][0],
            self._linedata[self._name_x_axis][-1],
        )

        for ax in self._axes:
            ax.relim()
            ax.autoscale(True, "y")

        if isinstance(self._linedata[self._name_x_axis][0], datetime):
            self._figure.autofmt_xdate()

        return list(line for lines in self._lines.values() for line in lines)

    @staticmethod
    def _synchronized_bridge(
        generator: AsyncGenerator[dict[str, Any], None]
    ) -> Generator[Optional[dict[str, Any]], None, None]:
        if not isinstance(generator, AsyncGenerator):
            raise TypeError

        loop = asyncio.new_event_loop()
        q: Queue[dict[str, Any]] = Queue()

        async def put(ag: AsyncGenerator[dict[str, Any], None]):
            async for value in ag:
                q.put(value)

        def run_loop(ag: AsyncGenerator[dict[str, Any], None]):
            asyncio.set_event_loop(loop)
            loop.run_until_complete(put(ag))

        thread = threading.Thread(target=run_loop, args=(generator,))
        thread.start()

        def bridged_generator() -> Generator[Optional[dict[str, Any]], None, None]:
            yield q.get()
            while loop.is_running() or not q.empty():
                try:
                    yield q.get_nowait()
                except EmptyQueueError:
                    yield None

        return bridged_generator()

    def show(
        self,
        interval: int = 25,
        save_count: int = 200,
        save_path: Optional[str] = None,
        *,
        blit: bool = False,
        sync_generate: bool = False,
        show_grid: bool = False,
    ) -> None:
        """
        Prepare everything and show. This method should be called at the last.
        """
        self._prepare_axes_and_lines(blit=blit, show_grid=show_grid)
        self._func_animation = pltanim.FuncAnimation(
            self._figure,
            self.update,
            frames=(
                self._synchronized_bridge(generate_async(**self._indicators_by_name))
                if not sync_generate
                else generate_sync(**self._indicators_by_name)
            ),
            interval=interval,
            blit=blit,
            repeat=False,
            save_count=save_count,
            cache_frame_data=False,
        )
        if save_path:
            self._func_animation.save(
                save_path,
                progress_callback=(
                    lambda i, n: print("Saving frame %03d/%03d" % (i, n))
                ),
            )
        plt.show()
