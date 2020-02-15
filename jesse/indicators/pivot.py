from collections import namedtuple

import numpy as np

from jesse.helpers import slice_candles

PIVOT = namedtuple('PIVOT', ['r4', 'r3', 'r2', 'r1', 'pp', 's1', 's2', 's3', 's4'])


def pivot(candles: np.ndarray, mode: int = 0, sequential: bool = False) -> PIVOT:
    """
    Pivot Points

    :param candles: np.ndarray
    :param mode: int - default = 0
    :param seq