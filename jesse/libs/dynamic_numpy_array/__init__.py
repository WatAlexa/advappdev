import numpy as np

from jesse.helpers import np_shift


class DynamicNumpyArray:
    """
    Dynamic Numpy Array

    A data structure containing a numpy array which expands its memory
    allocation every N number. Hence, it's both fast and dynamic.
    """

    def __init__(self, shape: tuple, drop_at: int = None):
        self.index = -1
        s