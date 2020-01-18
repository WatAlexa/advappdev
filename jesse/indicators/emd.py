from collections import namedtuple

import numpy as np
import talib
try:
    from numba import njit
except ImportError:
    njit = lambda a : a

from jesse.helpers import slice_candles

EMD = namedtuple('EMD', ['upperband', 'middleband', 'lowerband'])


def emd(candles: np.ndarray, period: int = 20, delta=0.5, fraction=0.1, sequential: bool = False) -> EMD:
    """
    Empirical Mode Decomposition by John F. Ehlers and Ric Way

    :param candles: np.ndarray
    :param period: int - default: 20
    :param delta: float - default: 0.5
    :param fraction: float - default: 0.1
    :param sequential: bool - default: False

    :return: EMD(upperband, middleband, lowerband)
    """
    candles = slice_candles(candles, sequential)

    price = (candles[:, 3] + candles[:, 4]) / 2

    bp = bp_fast(price, period, delta)

    mean = talib.SMA(bp, timeperiod=2 * period)
    peak, valley = peak_valley_fast(bp, price)

    avg_peak = fraction * talib.SMA(peak, timeperiod=50)
    avg_valley = fraction * talib.SMA(valley, timeperiod=50)

    if sequential:
        return EMD(avg_peak, mean, avg_valley)
    else:
        return EMD(avg_peak[-1], mean[-1], avg_valley[-1])


@njit
def bp_fast(price, period, delta):
    # bandpass filter
    beta = np.cos(2 * np.pi / period)
    gamma = 1 / np.cos(4 * np.pi * delta / period)
    alpha = gamma - np.sqrt(gamma * gamma - 1)
    bp = np.ze