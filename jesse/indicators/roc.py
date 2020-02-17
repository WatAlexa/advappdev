from typing import Union

import numpy as np
import talib

from jesse.helpers import get_candle_source
from jesse.helpers import slice_candles


def roc(candles: np.ndarray, period: int = 10, source_type: str = "close", sequential: bool = False) -> Union[
    float, np.ndarray]:
    """
    ROC - Rate of change : ((price/prevPrice)-1)*100

    :param candles: np.ndarray
    :param period: int - default: 10
    :param source_type