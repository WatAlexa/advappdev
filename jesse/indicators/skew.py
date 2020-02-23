from typing import Union

import numpy as np
from scipy import stats
from numpy.lib.stride_tricks import sliding_window_view

from jesse.helpers import get_candle_source, slice_candles, same_length


def skew(candles: np.ndarray, period: int = 5, source_type: str = "hl2", sequential: bool = False) -> Union[
    float, np.ndarray]:
    """
    Skewness

    