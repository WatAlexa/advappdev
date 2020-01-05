from random import randint
from typing import Union

import numpy as np

# 2021-01-01T00:00:00+00:00
first_timestamp = 1609459080000
open_price = randint(40, 100)
close_price = randint(open_price, 110) if randint(0, 1) else randint(
    30, open_price)
max_price = max(open_price, close_price)
high_price = max_price if randint(0, 1) else randint(max_price, max_price + 10)
min_price = min(open_price, close_price)
low_price = min_price if randint(0, 1) else randint(min_price, min_price + 10)


def range_candles(count: int) -> np.ndarray:
    """
    Generates a range of candles with random values.
    """
    fake_candle(reset=True)
    arr = np.zeros((count, 6))
    for i in range(count):
        arr[i] = fake_candle()
    return arr


def candles_from_close_prices(prices: Union[list, range]) -> np.ndarray:
    """
    Generates a range of candles from a list of close prices.
    The first candle has the timestamp of "2021-01-01T00:00:00+00:00"
    """
    fake_candle(reset=True)
    global first_timestamp
    arr = []
    prev_p = np.nan
    for p in prices:
        # first prev_p
        if np.isnan(prev_p):
            prev_p = p - 0.5

        first_timestamp += 60000
        open_p = prev_p
        close_p = p
        high_p = max(open_p, close_p)
        low_p = min(open_p, close_p)
        vol = randint(0, 200)

        arr.append([first_timestamp, open_p, close_p, high_p, low_p, vol])

        # save prev_p for next candle
        prev_p = 