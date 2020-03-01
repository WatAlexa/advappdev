from typing import Union

import numpy as np
import tulipy as ti

from jesse.helpers import get_candle_source, same_length
from jesse.helpers import slice_candles


def zlema(candles: np.ndarray, period: int = 20, source_type: str = "close", 