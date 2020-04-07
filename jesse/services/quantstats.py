import os
from datetime import datetime

import arrow
import pandas as pd
import quantstats as qs

from jesse.config import config
from jesse.store import store
import jesse.helpers as jh


def quantstats_tearsheet(buy_and_hold_returns: pd.Series, study_name: str) -> str:
    daily_returns = pd.Series(store.app.daily_balance).pct_change(1).values

    start_date = datetime.fromtimestamp(store.app.starting_time / 1000)
    date_index = pd.date_range(start=start_date, periods=len(store.app.daily_balance))

    returns_time_series = pd.Series(daily_returns, index=date_index)

    mode = config['app']['trading_mode']
    modes = {
        'backtest': ['BT', 'Backtest'],
        'livetrade': ['LT', 'LiveTrade'],
        'papertrade': ['PT', 'PaperTrade']
    }

    os.makedirs('./storage/full-reports', exist_ok=True)

    file_path = f'storage/full-reports/{jh.get_session_id()}.html'.replace(":", "-")

    title = f"{modes[mode][1]} → {arrow.utcnow().strftime('%d %b, %Y %H:%M:%S')} → {study_name}"

    try:
        qs.reports.html(returns=returns_time_series, periods_per_year=365, benchmark=buy_and_hold_returns, title=title, output=file_path)
    except IndexError:
        qs.reports.html(returns=returns_time_series, periods_per_year=365, title=title, output=file_path)
    except:
        raise

    return file_path


# from datetime import timedelta
# import quantstats.plots as _plots
# import quantstats.stats as _stats
# import quantstats.utils as _utils
# from quantstats.reports import _get_trading_periods, metrics
# import numpy as np
# def quantstats_api(benchmark: pd.Series) -> dict:
#     click.clear()
#
#     daily_returns = pd.Series(store.app.daily_balance).pct_change(1).values
#
#     start_date = datetime.fromtimestamp(store.app.starting_time / 1000)
#
#     date_index = pd.date_range(start=start_date, periods=len(store.app.daily_balance))
#
#     returns = pd.Series(daily_returns, index=date_index)
#
#     data = {}
#     periods_per_year = 365
#     rf = 0.
#     compounded = True
#
#     win_year, win_half_year = _get_trading_periods()
#
#     # prepare timeseries
#     returns = _utils._prepare_returns(returns)
#
#     date_range = returns.index.strftime('%e %b, %Y')
#
#     data['date_range'] = f'{date_range[0]} - {date_range[-1]}'
#
#     if benchmark is not None:
#         benchmark = _utils._prepare_benchmark(benchmark, returns.index, rf)
#
#     mtrx = metrics(returns=returns, benchmark=benchmark,
#                    rf=rf, display=False, mode='full',
#                    sep=True, internal="True",
#                    compounded=compounded,
#                    periods_per_year=periods_per_year,
#                    prepare_returns=False)[2:]
#
#     mtrx.index.name = 'Metric'
#     data['metrics'] = mtrx
#
#     if benchmark is not None:
#         yoy = _stats.compare(
#             returns, benchmark, "A", compounded=compounded,
#             prepare_returns=False)
#         yoy.columns = ['Benchmark', 'Strategy', 'Multiplier', 'Won']
#         yoy.index.name = 'Year'
#     else:
#         # pct multiplier
#         yoy = pd.DataFrame(
#             _utils.group_returns(returns, returns.index.year) * 100)
#         yoy.columns = ['Return']
#         yoy['Cumulative'] = _utils.group_returns(
#             returns, returns.index.year, True)
#         yoy['Return'] = yoy['Return'].round(2).astype(str) + '%'
#         yoy['Cumulative'] = (yoy['Cumulative'] *
#                              100).round(2).astype(str) + '%'
#         yoy.index.name = 'Year'
#
#     data['yoy'] = yoy
#
#     dd = _stats.to_drawdown_series(returns)
#     dd_info = _stats.drawdown_details(dd).sort_values(
#         by='max drawdown', ascending=True)[:10]
#
#     dd_info = dd_info[['start', 'end', 'max drawdown', 'days']]
#     dd_info.columns = ['Started', 'Recovered', 'Drawdown', 'Days']
#
#     data['dd_info'] = dd_info
#
#     data['monthly_returns'] = _stats.monthly_returns(returns, eoy=False,
#                                                      compounded=compounded) * 100
#
#     plot_returns = _plots.returns(returns, benchmark,
#                                   figsize=(8, 5), subtitle=False,
#                                   show=False, ylabel=False, cumulative=compounded,
#                                   prepare_returns=False)
#
#     # Get the data from the figure
#     data['plot_returns_strategy'] = plot_returns.get_axes()[0].get_lines()[0].get_data()
#
#     if benchmark is not None:
#         data['plot_returns_benchmark'] = plot_returns.get_axes()[0].get_lines()[1].get_data()
#
#     plot_log_returns = _plots.log_returns(returns, benchmark,
#                                           figsize=(8, 4), subtitle=False,
#                                           show=False, ylabel=False, cumulative=compounded,
#                                           prepare_returns=False)
#
#     # Get the data from the figure
#     data['plot_log_returns_strategy'] = plot_log_returns.get_axes()[0].get_lines()[0].get_data()
#
#     if benchmark is not None:
#         data['plot_log_returns_benchmark'] = plot_log_returns.get_axes()[0].get_lines()[1].get_data()
#
#     if benchmark is not None:
#         vol_returns = _plots.returns(returns, benchmark, match_volatility=True, figsize=(8, 4), subtitle=False,
#                                      show=False, ylabel=False, cumulative=compounded,
#                                      prepare_returns=False)
#         # Get