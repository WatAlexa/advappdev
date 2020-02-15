from typing import Union

import numpy as np
from jesse.indicators.ma import ma

from jesse.helpers import get_candle_source
from jesse.helpers import slice_candles


def ppo(candles: np.ndarray, fast_period: int = 12, slow_period: int = 26, matype: int = 0, source_type: str = "close",
        sequential: bool = False) -> Union[float, np.ndarray]:
    """
    PPO - Percentage Price Oscillator

    :param candles: np.ndarray
    :param fast_period: int - default: 12
    :param slow_period: int - default: 26
    :param matype: int - default: 0
    :par