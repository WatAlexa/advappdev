"""
For the multiprocessing to work property, it's best to pass around pure functions into workers instead
of methods of a class. Below functions have been designed with that in mind.
"""
from math import log10
import jesse.helpers as jh
from jesse.research.backtest import _isolated_backtest as isolated_backtest
from jesse.services import logger
import os
from random import randint, choice
import numpy as np


def _formatted_inputs_for_isolated_backtest(user_config, routes):
    return {
        'starting_balance': user_config['exchange']['balance'],
        'fee': user_config['exchange']['fee'],
        'type': user_config['exchange']['type'],
        'futures_leverage': user_config['exchange']['futures_leverage'],
        'futures_leverage_mode': user_config['exchange']['futures_leverage_mode'],
        'exchange': routes[0]['exchange'],
        'warm_up_candles': user_config['warmup_candles_num']
    }


def get_fitness(
        optimization_config: dict, routes: list, extra_routes: list, strategy_hp, dna: str, training_candles,
        testing_candles, optimal_total
) -> tuple:
    """
    Notice that this function is likely to be executed inside workers, hence its inputs must
    have everything required for it to run. So it cannot access store, config, etc
    """
    hp = jh.dna_to_hp(strategy_hp, dna)

    # run backtest simulation
    try:
        training_data_metrics = isolated_backtest(
            _formatted_inputs_for_isolated_backtest(optimization_config, routes),
            routes,
            extra_routes,
            training_candles,
            hyperparameters=hp
        )['metrics']
    except Exception as e:
        # get the main title of the exception
        log_text = e
        log_text = f"Exception in strategy execution:\n {log_text}"
        logger.log_optimize_mode(log_text)
        raise e

    training_log = {'win-rate': None, 'total': None, 'PNL': None}
    testing_log = {'win-rate': None, 'total': None, 'PNL': None}

    # TODO: some of these have to be dynamic based on how many days it's trading for like for example "total"
    if training_data_metrics['total'] > 5:
        total_effect_rate = log10(training_data_metrics['total']) / log10(optimal_total)
        total_effect_rate = min(total_effect_rate, 1)
        ratio_config = jh.get_config('env.optimization.ratio', 'sharpe')
        if ratio_config == 'sharpe':
            ratio = training_data_metrics['sharpe_ratio']
            ratio_normalized = jh.normalize(ratio, -.5, 5)
        elif ratio_config == 'calmar':
            ratio = training_data_metrics['calmar_ratio']
            ratio_normalized = jh.normalize(ratio, -.5, 30)
        elif ratio_config == 'sortino':
            ratio = training_data_metrics['sortino_ratio']
            ratio_normalized = jh.normalize(ratio, -.5, 15)
        elif ratio_config == 'omega':
            ratio = training_data_metrics['omega_ratio']
            ratio_normalized = jh.normalize(ratio, -.5, 