from typing import Union

import numpy as np
import talib

from jesse.helpers import slice_candles


def typprice(candles: np.ndarray, sequential: bool = False) -> Union[float, np.ndarray]:
    """
    TYPPRICE - Typical Price

    :para