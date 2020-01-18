from typing import Union

import numpy as np
import talib

import jesse.helpers as jh
from jesse.helpers import slice_candles


def dti(candles: np.ndarray, r: int = 14, s: int = 10, u: int = 5, sequential: bool = False) -> Union[
    float, np.ndarray]:
    """
    DTI by William Blau

    :param candles: np.ndarray
    :param r: int - default: 14
    :param s: int - default: 10
    :param u: int - default: 5
    :param sequential: bool - default: False

    :return: float
    """
    candles = slice_candles(candles, sequential)

    high = candles[:, 3]
    low = candles[:, 4]

    high_1 = jh.np_shift(high, 1, np.nan)
    low_1 = jh.np_shift(low, 1, np.nan)

    xHMU = np.where(high - high_1 > 0, high - high_1, 0