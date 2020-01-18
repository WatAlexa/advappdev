from typing import Union

import numpy as np
import talib
from scipy.ndimage.filters import maximum_filter1d, minimum_filter1d

from jesse.helpers import slice_candles


def chande(candles: np.ndarray, period: int = 22, mult: float = 3.0, direction: str = "long",
           sequential: bool = False) -> Union[float, np.ndarray]:
    """
    Chandelier Exits

    :param candles: np.ndarray
    :param period: int - default: 22
    :param mult: float - default: 3.0
    :param direction: str - default: "long"
    :param sequential: bool - default: False

    :return: float | np.ndarray
    """
    candles = slice_candles(candles, sequential)

    candles_close = candles[:, 2]
    candles_high = candles[:, 3]
    candles_low = candles[:, 4]

    atr = talib.ATR(candles_high, candles_low, candles_close, timeperiod=period)

    if direction == 'long':
        maxp = 