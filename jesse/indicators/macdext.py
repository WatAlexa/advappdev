from collections import namedtuple

import numpy as np

from jesse.helpers import get_candle_source, slice_candles, same_length
from jesse.indicators.ma import ma

MACDEXT = namedtuple('MACDEXT', ['macd', 'signal', 'hist'])


def macdext(candles: np.ndarray, fast_period: int = 12, fast_matype: int = 0, slow_period: int = 26,
            slow_matype: int = 0, signal_period: int = 9, signal_matype: int = 0, source_type: str = "close",
            sequential: bool = False) -> MACDEXT:
    """
    MACDEXT - MACD with controllable MA type

    :param candles: np.ndarray
    :param fast_period: int - default: 12
    :param fast_matype: int - default: 0
    :param slow_period: int - default: 26
    :param slow_matype: int - default: 0
    :param signal_period: int - default: 9
    :param signal_matype: int - default: 0
    :param source_type: str - default: "close"
    :param sequential: bool - default: False

    :return: MACDEXT(macd, signal, hist)
    """
    candles = slice_candles(candles, sequential)

    if fast_matype == 29 or slow_matype == 29 or signal_matype == 29:
        raise