import threading
import numpy as np

import jesse.helpers as jh
from jesse.services import logger


def store_candle_into_db(exchange: str, symbol: str, timeframe: str, candle: np.ndarray, on_conflict='ignore') -> None:
    from jesse.models.Candle import Candle

    d = {
        'id': jh.generate_unique_id(),
        'exchange': exchange,
        'symbol': symbol,
        'timeframe': timeframe,
        'timestamp': candle[0],
        'open': candle[1],
        'high': candle[3],
        'low': candle[4],
        'close': candle[2],
        'volume': candle[5]
    }

    if on_conflict == 'ignore':
        Candle.insert(**d).on_conflict_ignore().execute()
    elif on_conflict == 'replace':
        Candle.insert(**d).on_conflict(
            conflict_target=['exchange', 'symbol', 'timeframe', 'timestamp'],
            preserve=(Candle.open, Candle.high, Candle.low, Candle.close, Candle.volume),
        ).execute()
    elif on_conflict == 'error':
        Candle.insert(**d).execute()
    else:
        raise Exception(f'Unknown on_conflict value: {on_conflict}')


def store_candles_into_db(exchange: str, symbol: str, timeframe: str, candles: np.ndarray, on_conflict='ignore') -> None:
    # make sure the number of candles is more than 0
    if len(candles) == 0:
        raise Exception(f'No candles to store for {exchange}-{symbol}-{timeframe}')

    from jesse.models import Candle

    # convert candles to list of dicts
    candles_list = []
    for candle in candles:
        d = {
            'id': jh.generate_unique_id(),
            'symbol': symbol,
            'exchange': exchange,
            'timestamp': candle[0],
            'open': candle[1],
            'high': candle[3],
            'low': candle[4],
            'close': candle[2],
            'volume': candle[5],
            'timeframe': timeframe,
        }
        candles_list.append(d)

    if on_conflict == 'ignore':
        Candle.insert_many(candles_list).on_conflict_ignore().execute()
    elif on_conflict == 'replace':
        Candle.insert_many(candles_list).on_conflict(
            conflict_target=['exchange', 'symbol', 'timeframe', 'timestamp'],
            preserve=(Candle.open, Candle.high, Candle.low, Candle.close, Candle.volume),
        ).execute()
    elif on_conflict == 'error':
        Candle.insert_many(candles_list).execute()
    else:
        raise Exception(f'Unknown on_conflict value: {on_conflict}')


def store_log_into_db(log: dict, log_type: str) -> None:
    from jesse.store import store
    from jesse.models.Log import Log

    if log_type == 'info':
        log_type = 1
    elif log_type == 'error':
        log_type = 2
    else:
        raise ValueError(f"Unsupported log_type value: {log_type}")

    d = {
        'id': log['id'],
        'session_id': store.app.session_id,
        'type': log_type,
        'timestamp': log['timestamp'],
        'message': log['message']
    }

    Log.insert(**d).execute()


def store_ticker_into_db(exchange: str, symbol: str, ticker: np.ndarray) -> None:
    return
    from jesse.models.Ticker import Ticker

    d = {
        'id': jh.generate_unique_id(),
        'timestamp': ticker[0],
        'last_price': ticker[1],
        'high_price': ticker[2],
        'low_price': ticker[3],
        'volume': ticker[4],
        'symbol': symbol,
        'exchange': exchange,
    }

    def async_save() -> None:
        Ticker.insert(**d).on_conflict_ignore().execute()
        print(
            jh.color(f'ticker: {jh.timestamp_to_time(d["timestamp"])}-{exchange}-{symbol}: {ticker}', 'yellow')
        )

    # async call
    threading.Thread(target=async_save).start()


def store_completed_trade_into_db(completed_trade) -> No