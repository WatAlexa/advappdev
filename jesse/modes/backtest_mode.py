import time
from typing import Dict, Union, List

import arrow
import numpy as np
import pandas as pd

import jesse.helpers as jh
import jesse.services.metrics as stats
import jesse.services.required_candles as required_candles
import jesse.services.selectors as selectors
from jesse import exceptions
from jesse.config import config
from jesse.enums import timeframes, order_types
from jesse.models import Candle, Order, Position
from jesse.modes.utils import save_daily_portfolio_balance
from jesse.routes import router
from jesse.services import charts
from jesse.services import quantstats
from jesse.services import report
from jesse.services.cache import cache
from jesse.services.candle import generate_candle_from_one_minutes, print_candle, candle_includes_price, split_candle
from jesse.services.file import store_logs
from jesse.services.validators import validate_routes
from jesse.store import store
from jesse.services import logger
from jesse.services.failure import register_custom_exception_handler
from jesse.services.redis import sync_publish, process_status
from timeloop import Timeloop
from datetime import timedelta
from jesse.services.progressbar import Progressbar


def run(
        debug_mode,
        user_config: dict,
        routes: List[Dict[str, str]],
        extra_routes: List[Dict[str, str]],
        start_date: str,
        finish_date: str,
        candles: dict = None,
        chart: bool = False,
        tradingview: bool = False,
        full_reports: bool = False,
        csv: bool = False,
        json: bool = False
) -> None:
    if not jh.is_unit_testing():
        # at every second, we check to see if it's time to execute stuff
        status_checker = Timeloop()
        @status_checker.job(interval=timedelta(seconds=1))
        def handle_time():
            if process_status() != 'started':
                raise exceptions.Termination
        status_checker.start()

    from jesse.config import config, set_config
    config['app']['trading_mode'] = 'backtest'

    # debug flag
    config['app']['debug_mode'] = debug_mode

    # inject config
    if not jh.is_unit_testing():
        set_config(user_config)

    # set routes
    router.initiate(routes, extra_routes)

    store.app.set_session_id()

    register_custom_exception_handler()

    # validate routes
    validate_routes(router)

    # initiate candle store
    store.candles.init_storage(5000)

    # load historical candles
    if candles is None:
        candles = load_candles(start_date, finish_date)

    if not jh.should_execute_silently():
        sync_publish('general_info', {
            'session_id': jh.get_session_id(),
            'debug_mode': str(config['app']['debug_mode']),
        })
        # candles info
        key = f"{config['app']['considering_candles'][0][0]}-{config['app']['considering_candles'][0][1]}"
        sync_publish('candles_info', stats.candles_info(candles[key]['candles']))
        # routes info
        sync_publish('routes_info', stats.routes(router.routes))

    # run backtest simulation
    result = simulator(
        candles,
        run_silently=jh.should_execute_silently(),
        generate_charts=chart,
        generate_tradingview=tradingview,
        generate_quantstats=full_reports,
        generate_csv=csv,
        generate_json=json,
        generate_equity_curve=True,
        generate_hyperparameters=True
    )

    if not jh.should_execute_silently():
        sync_publish('alert', {
            'message': f"Successfully executed backtest simulation in: {result['execution_duration']} seconds",
            'type': 'success'
        })
        sync_publish('hyperparameters', result['hyperparameters'])
        sync_publish('metrics', result['metrics'])
        sync_publish('equity_curve', result['equity_curve'])

    # close database connection
    from jesse.services.db import database
    database.close_connection()


def _generate_quantstats_report(candles_dict: dict) -> str:
    if store.completed_trades.count == 0:
        return None

    price_data = []
    timestamps = []
    # load close candles for Buy and hold and calculate pct_change
    for index, c in enumerate(config['app']['considering_candles']):
        exchange, symbol = c[0], c[1]
        if exchange in config['app']['trading_exchanges'] and symbol in config['app']['trading_symbols']:
            candles = candles_dict[jh.key(exchange, symbol)]['candles']

            if timestamps == []:
                timestamps = candles[:, 0]
            price_data.append(candles[:, 1])

    price_data = np.transpose(price_data)
    price_df = pd.DataFrame(
        price_data, index=pd.to_datetime(timestamps, unit="ms"), dtype=float
    ).resample('D').mean()
    price_pct_change = price_df.pct_change(1).fillna(0)
    buy_and_hold_daily_returns_all_routes = price_pct_change.mean(1)
    study_name = _get_study_name()
    res = quantstats.quantstats_tearsheet(buy_and_hold_daily_returns_all_routes, study_name)
    return res


def _get_study_name() -> str:
    routes_count = len(router.routes)
    more = f"-and-{routes_count - 1}-more" if routes_count > 1 else ""
    if type(router.routes[0].strategy_name) is str:
        strategy_name = router.routes[0].strategy_name
    else:
        strategy_name = router.routes[0].strategy_name.__name__
    study_name = f"{strategy_name}-{router.routes[0].exchange}-{router.routes[0].symbol}-{router.routes[0].time