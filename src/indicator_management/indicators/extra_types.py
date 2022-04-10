from numbers import Number
from typing import Optional, Protocol, SupportsFloat, Union

Numeric = Union[Number, SupportsFloat]


class NumericOperationProtocol(Protocol):
    def __call__(self, *numbers: Numeric) -> Optional[Numeric]:
        raise NotImplementedError
