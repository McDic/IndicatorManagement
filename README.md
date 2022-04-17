# IndicatorManagement

This library provides management of mathematical/financial indicators, without having any problem on large amount of series data. Please look `Features` to see more details.

# Dependencies

- Python 3.10+
    - [sortedcontainers](https://github.com/grantjenks/python-sortedcontainers)
    - [matplotlib](https://github.com/matplotlib/matplotlib)

I am planning to support lower Python version.

# Installation

This module is available at [PyPI](https://pypi.org/project/indicator-management/), so you can download it via pip;

```
pip install --upgrade indicator-management
```

# Features

## Generate any indicators from any sources

You can generate any indicators you want. Here is a simple example.

```python
from pprint import pprint
import random

from indicator_management import generate_sync
from indicator_management.indicators import (
    RawSeriesIndicator as Raw,
    ExponentialMovingAverage as EMA,
)

i1 = Raw(raw_values=range(5))
i2 = i1 * 2 + 50
i3 = EMA(i2)

pprint(list(generate_sync(i1=i1, i2=i2, i3=i3)))
```

The code above will print following;

```
[{'i1': 0, 'i2': 50, 'i3': 50},
 {'i1': 1, 'i2': 52, 'i3': 50.19047619047619},
 {'i1': 2, 'i2': 54, 'i3': 50.55328798185941},
 {'i1': 3, 'i2': 56, 'i3': 51.072022459777564},
 {'i1': 4, 'i2': 58, 'i3': 51.73182984456066}]
```

As you can see, you can mix any operations or indicators to generate your own indicator.

## Plot your own indicators with convenience

[This code](https://github.com/McDic/IndicatorManagement/blob/master/examples/dynamic_plotting/app.py) will plot following graph;

![dynamic_plotting](https://i.imgur.com/j2wuuDb.gif)

As you can see, you can plot your indicators with convenience.

## Summarization

1. You can mix many operations to generate your own indicators. (As you can see from example code above.)

2. You can easily integrate your source with it.
You just have to prepare generator or asynchronous generator which yields values, wrap them in `RawSeriesIndicator` or `AsyncRawSeriesIndicator`, and then perform arbitrary operation to make your own indicator with your data sources.

3. You can inherit base classes of library's abstract indicators so you can perform any kind of complex operations.
I will write documentation for such advanced features.

4. There are some number of functions and classes which pre-defines existing indicators, like [RSI](https://www.investopedia.com/terms/r/rsi.asp), [MACD](https://www.investopedia.com/terms/m/macd.asp), [BB](https://www.investopedia.com/terms/b/bollingerbands.asp), etc.
I aim to make even more financial indicators to be built-in optimized in future.

5. This library stores only moving window of total data, so in case you process millions or even billions of data, you don't have to care about memory limit.

6. You can even plot your indicators by just defining indicators and pass those to `DataAnimator`, then the plotting will be automatically handled.

But, if you are interested in processing relatively small amount of data(Daily OHLCV for example) and interested in huge performance, then you can select alternative libraries like [TA-lib](https://github.com/mrjbq7/ta-lib).

# Any contributions are welcome!

Any contributions are surely welcome! Following are list of major TODOs;

- Make better documentation
- Implement more financial indicators
- Internal optimizations

I am open to all kind of discussions. Don't hesitate to begin any discussion for this project!

# Warning

This library is still under pre-alpha development, and API will be frequently changed.
