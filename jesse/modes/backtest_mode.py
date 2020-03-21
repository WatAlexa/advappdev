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
    study_name = f"{strategy_name}-{router.routes[0].exchange}-{router.routes[0].symbol}-{router.routes[0].timeframe}{more}"
    return study_name


def load_candles(start_date_str: str, finish_date_str: str) -> Dict[str, Dict[str, Union[str, np.ndarray]]]:
    start_date = jh.date_to_timestamp(start_date_str)
    finish_date = jh.date_to_timestamp(finish_date_str) - 60000

    # validate
    if start_date == finish_date:
        raise ValueError('start_date and finish_date cannot be the same.')
    if start_date > finish_date:
        raise ValueError('start_date cannot be bigger than finish_date.')
    if finish_date > arrow.utcnow().int_timestamp * 1000:
        raise ValueError(
            "Can't load candle data from the future! The finish-date can be up to yesterday's date at most.")

    # load and add required warm-up candles for backtest
    if jh.is_backtesting():
        for c in config['app']['considering_candles']:
            exchange, symbol = c[0], c[1]
            required_candles.inject_required_candles_to_store(
                required_candles.load_required_candles(exchange, symbol, start_date_str, finish_date_str),
                exchange,
                symbol
            )

    # download candles for the duration of the backtest
    candles = {}
    for c in config['app']['considering_candles']:
        exchange, symbol = c[0], c[1]

        key = jh.key(exchange, symbol)

        cache_key = f"{start_date_str}-{finish_date_str}-{key}"
        cached_value = cache.get_value(cache_key)
        # if cache exists use cache_value
        # not cached, get and cache for later calls in the next 5 minutes
        # fetch from database
        candles_tuple = cached_value or Candle.select(
                Candle.timestamp, Candle.open, Candle.close, Candle.high, Candle.low,
                Candle.volume
            ).where(
                Candle.exchange == exchange,
                Candle.symbol == symbol,
                Candle.timeframe == '1m' or Candle.timeframe.is_null(),
                Candle.timestamp.between(start_date, finish_date)
            ).order_by(Candle.timestamp.asc()).tuples()
        # validate that there are enough candles for selected period
        required_candles_count = (finish_date - start_date) / 60_000
        if len(candles_tuple) == 0 or candles_tuple[-1][0] != finish_date or candles_tuple[0][0] != start_date:
            raise exceptions.CandleNotFoundInDatabase(
                f'Not enough candles for {symbol}. You need to import candles.'
            )
        elif len(candles_tuple) != required_candles_count + 1:
            raise exceptions.CandleNotFoundInDatabase(
                f'There are missing candles between {start_date_str} => {finish_date_str}')

        # cache it for near future calls
        cache.set_value(cache_key, tuple(candles_tuple), expire_seconds=60 * 60 * 24 * 7)

        candles[key] = {
            'exchange': exchange,
            'symbol': symbol,
            'candles': np.array(candles_tuple)
        }

    return candles


def simulator(
        candles: dict,
        run_silently: bool,
        hyperparameters: dict = None,
        generate_charts: bool = False,
        generate_tradingview: bool = False,
        generate_quantstats: bool = False,
        generate_csv: bool = False,
        generate_json: bool = False,
        generate_equity_curve: bool = False,
        generate_hyperparameters: bool = False,
) -> dict:
    result = {}
    begin_time_track = time.time()
    key = f"{config['app']['considering_candles'][0][0]}-{config['app']['considering_candles'][0][1]}"
    first_candles_set = candles[key]['candles']
    length = len(first_candles_set)
    # to preset the array size for performance
    try:
        store.app.starting_time = first_candles_set[0][0]
    except IndexError:
        raise IndexError('Check your "warm_up_candles" config value')
    store.app.time = first_candles_set[0][0]

    # initiate strategies
    for r in router.routes:
        # if the r.strategy is str read it from file
        if isinstance(r.strategy_name, str):
            StrategyClass = jh.get_strategy_class(r.strategy_name)
        # else it is a class object so just use it
        else:
            StrategyClass = r.strategy_name

        try:
            r.strategy = StrategyClass()
        except TypeError:
            raise exceptions.InvalidStrategy(
                "Looks like the structure of your strategy directory is incorrect. Make sure to include the strategy INSIDE the __init__.py file. Another reason for this error might be that your strategy is missing the mandatory methods such as should_long(), go_long(), and should_cancel_entry(). "
                "\nIf you need working examples, check out: https://github.com/jesse-ai/example-strategies"
            )
        except:
            raise

        r.strategy.name = r.strategy_name
        r.strategy.exchange = r.exchange
        r.strategy.symbol = r.symbol
        r.strategy.timeframe = r.timeframe

        # read the dna from strategy's dna() and use it for injecting inject hyperparameters
        # first convert DNS string