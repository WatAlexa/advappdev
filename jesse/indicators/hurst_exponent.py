import numpy as np

try:
    from numba import njit
except ImportError:
    njit = lambda a : a

from jesse.helpers import get_candle_source, slice_candles
from scipy import signal

def hurst_exponent(candles: np.ndarray, min_chunksize: int = 8, max_chunksize: int = 200, num_chunksize:int=5, method:int=1, source_type: str = "close") -> float:
    """
    Hurst Exponent

    :param candles: np.ndarray
    :param min_chunksize: int - default: 8
    :param max_chunksize: int - default: 200
    :param num_chunksize: int - default: 5
    :param method: int - default: 1 - 0: RS | 1: DMA | 2: DSOD
    :param source_type: str - default: "close"

    :return: float
    """

    if len(candles.shape) == 1:
      source = candles
    else:
      candles = slice_candles(candles, False)
      source = get_candle_source(candles, source_type=source_type)

    if method == 0:
        h = hurst_rs(np.diff(source), min_chunksize, max_chunksize, num_chunksize)
    elif method == 1:
        h = hurst_dma(source, min_chunksize, max_chunksize, num_chunksize)
    elif method == 2:
        h = hurst_dsod(source)
    else:
        raise NotImplementedError('The method choose is not implemented.')

    return None if np.isnan(h) else h


@njit
def hurst_rs(x, min_chunksize, max_chunksize, num_chunksize):
    """Estimate the Hurst exponent using R/S method.
    Estimates the Hurst (H) exponent using the R/S method from the time series.
    The R/S method consists of dividing the series into pieces of equal size
    `series_len` and calculating the rescaled range. This repeats the process
    for several `series_len` values and adjusts data regression to obtain the H.
    `series_len` will take values between `min_chunksize` and `max_chunksize`,
    the step size from `min_chunksize` to `max_chunksize` can be controlled
    through the parameter `step_chunksize`.
    Parameters
    ----------
    x : 1D-array
        A time series to calculate hurst exponent, must have more elements
        than `min_chunksize` and `max_chunksize`.
    min_chunksize : int
        This parameter allow you control the minimum window size.
    max_chunksize : int
        This parameter allow you control the maximum window size.
    num_chunksize : int
        This parameter allow you control the size of the step from minimum to
        maximum window size. Bigger step means fewer calculations.
    out : 1-element-array, optional
        one element array to store the output.
    Returns
    -------
    H : float
        A estimation of Hurst exponent.
    References
    ----------
    Hurst, H. E. (1951). Long term storage capacity of reservoirs. ASCE
    Transactions, 116(776), 770-808.
    Alessio, E., Carbone, A., Castelli, G. et al. Eur. Phys. J. B (2002) 27:
    197. http://dx.doi.org/10.1140/epjb/e20020150
    """
    N = len(x)
    max_chunksize += 1
    rs_tmp = np.empty(N, dtype=np.float64)
    chunk_size_list = np.linspace(min_chunksize, max_chunksize, num_chunksize) \
        .astype(np.int64)
    rs_values_list = np.empty(num_chunksize, dtype=np.float64)

    # 1. The series is divided into chunks of chunk_size_list size
    for i in range(num_chunksize):
        chunk_size = chunk_size_list[i]

        # 2. it iterates on the indices of the first observation of each chunk
        number_of_chunks = int(len(x) / chunk_size)

        for idx in range(number_of_chunks):
            # next means no overlapping
            # convert index to index selection of each chunk
            ini = idx * chunk_size
            end = ini + chunk_size
            chunk = x[ini:end]

            # 2.1 Calculate the RS (chunk_size)
            z = np.cumsum(chunk - np.mean(chunk))
            rs_tmp[idx] = np.divide(
                np.max(z) - np.min(z),  # range
                np.nanstd(chunk)  # standar deviation
            )

        # 3. Average of RS(chunk_size)
        rs_values_list[i] = np.nanmean(rs_tmp[:idx + 1])

    # 4. calculate the Hurst exponent.
    H, c = np.linalg.lstsq(
        a=np.vstack((np.log(chunk_size_list), np.ones(num_chunksize))).T,
        b=np.log(rs_values_list)
    )[0]

    return H

def hurst_dma(prices, min_chunksize=8, max_chunksize=200, num_chunksize=5):
    """Estimate the Hurst exponent using R/S method.

    Estimates the Hurst (H) exponent using the DMA method from the time series.
    The DMA method consists on calculate the moving average of size `series_len`
    and subtract it to the original series an