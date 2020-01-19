from collections import namedtuple

import numpy as np
import talib

from jesse.helpers import get_candle_source
from jesse.helpers import slice_candles

SINEWAVE = namedtuple('SINEWAVE', ['sin