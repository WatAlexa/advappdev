from datetime import datetime, timedelta
from typing import List, Any, Union

import numpy as np
import pandas as pd
from quantstats import stats

import jesse.helpers as jh
from jesse.models import ClosedTrade
from jesse.store import store
from jesse.services import selectors


def candles_info(candles_array: np.ndarray) -> dict:
    period = jh.date_diff_in_days(
        jh.timestamp_to_arrow(candles_array[0][0]),
        jh.timestamp_to_arrow(candles_array[-1][0])) + 1

    if period > 365:
        duration = f'{period} days ({round(period / 365, 2)} years)'
    elif period > 30:
        duration = f'{period} days ({round(period / 30, 2)} months)'
    else:
        duration = f'{period} days'

    # type of the exchange
    trading_exchange = selectors.get_trading_exchange()

    info = {
        'duration': duration,
        'starting_time': candles_array[0][0],
        'finishing_time': (candles_array[-1][0] + 60_000),
        'exchange_type': trading_exchange.type,
    }

    # if the exchange type is futures, also display leverage
    if trading_exchange.type == 'futures':
        info['leverage'] = trading_exchange.futures_leverage
        info['leverage_mode'] = trading_exchange.futures_leverage_mode

    return info


def routes(routes_arr: list) -> list:
    return [{
            'exchange': r.exchange,
            'symbol': r.symbol,
            'timeframe': r.timeframe,
            'strategy_name': r.strategy_name,
        } for r in routes_arr]


def trades(trades_list: List[ClosedTrade], daily_balance: list, final: bool = True) -> dict:
    starting_balance = 0
    current_balance = 0

    for e in store.exchanges.storage:
        starting_balance += store.exchanges.storage[e].starting_assets[jh.app_currency()]
        current_balance += store.exchanges.storage[e].assets[jh.app_currency()]

    if not trades_list:
        return {'total': 0, 'win_rate': 0, 'net_profit_percentage': 0}

    df = pd.DataFrame.from_records([t.to_dict for t in trades_list])

    total_completed = len(df)
    winning_trades = df.loc[df['PNL'] > 0]
    total_winning_trades = len(winning_trades)
    losing_trades = df.loc[df['PNL'] < 0]
    total_losing_trades = len(losing_trades)

    arr = df['PNL'].to_numpy()
    pos = np.clip(arr, 0, 1).astype(bool).cumsum()
    neg = np.clip(arr, -1, 0).astype(bool).cumsum()
    current_streak = np.where(arr >= 0, pos - np.maximum.accumulate(np.where(arr <= 0, pos, 0)),
                              -neg + np.maximum.accumulate(np.where(arr >= 0, neg, 0)))

    s_min = current_streak.min()
    losing_streak = 0 if s_min > 0 else abs(s_min)

    s_max = current_streak.max()
    winning_streak = max(s_max, 0)

    largest_losing_trade = 0 if total_losing_trades == 0 else losing_trades['PNL'].min()
    largest_winning_trade = 0 if total_winning_trades == 0 else winning_trades['PNL'].max()
    if len(winning_trades) == 0:
        win_rate = 0
    else:
        win_rate = len(winning_trades) / (len(losing_trades) + len(winning_trades))
    longs_count = len(df.loc[df['type'] == 'long'])
    shorts_count = len(df.loc[df['type'] == 'short'])
    longs_percentage = longs_count / (longs_count + shorts_count) * 100
    shorts_percentage = 100 - longs_percentage
    fee = df['fee'].sum()
    net_profit = df['PNL'].sum()
    net_profit_percentage = (net_profit / starting_balance) * 100
    average_win = winning_trades['PNL'].mean()
    average_loss = abs(losing_trades['PNL'].mean())
    ratio_avg_win_loss = average_win / average_loss
    expectancy = (0 if np.isnan(average_win) else average_win) * win_rate - (
        0 if np.isnan(average_loss) else average_loss) * (1 - win_rate)
    expectancy = expectancy
    expectancy_percentage = (expectancy / starting_balance) * 100
    expected_net_profit_every_100_trades = expectancy_percentage * 100
    average_holding_period = df['holding_period'].mean()
    average_winning_holding_period = winning_trades['holding_period'].mean()
    average_losing_holding_period = losing_trades['holding_period'].mean()
    gross_profit = winning_trades['PNL'].sum()
    gross_loss = losing_trades['PNL'].sum()

    start_date = datetime.fromtimestamp(store.app.starting_time / 1000)
    date_index = pd.date_range(start=start_date, periods=len(daily_balance))

    daily_return = pd.DataFrame(daily_balance, index=date_index).pct_change(1)

    total_open_trades = store.app.total_open_trades
    open_pl = store.app.total_open_pl


    max_drawdown