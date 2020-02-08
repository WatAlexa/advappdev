from typing import Union

import numpy as np
try:
    from numba import njit
except ImportError:
    njit = lambda a