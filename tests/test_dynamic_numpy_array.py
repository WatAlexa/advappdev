
import numpy as np
import pytest

from jesse.libs import DynamicNumpyArray


def test_append():
    a = DynamicNumpyArray((10, 6))
    a.append(np.array([1, 2, 3, 4, 5, 6]))
    assert a.index == 0
    assert a.array[0][0] == 1
    assert a.array[0][1] == 2
    assert a.array[0][2] == 3
    assert a.array[0][3] == 4
    assert a.array[0][4] == 5
    assert a.array[0][5] == 6

    a.append(np.array([7, 8, 9, 10, 11, 12]))
    assert a.index == 1
    assert a.array[1][0] == 7
    assert a.array[1][1] == 8
    assert a.array[1][2] == 9
    assert a.array[1][3] == 10
    assert a.array[1][4] == 11
    assert a.array[1][5] == 12


def test_flush():
    a = DynamicNumpyArray((10, 6))
    a.append(np.array([1, 2, 3, 4, 5, 6]))
    a.append(np.array([7, 8, 9, 10, 11, 12]))
    assert a.index == 1
    assert a.array[0][0] == 1
    assert a.array[1][0] == 7

    a.flush()

    assert a.index == -1
    assert a.array[0][0] == 0
    assert a.array[1][0] == 0


def test_get_last_item():
    a = DynamicNumpyArray((10, 6))

    with pytest.raises(IndexError):
        a.get_last_item()

    a.append(np.array([1, 2, 3, 4, 5, 6]))
    a.append(np.array([7, 8, 9, 10, 11, 12]))
    assert a.index == 1
    assert a.array[0][0] == 1
    assert a.array[1][0] == 7
