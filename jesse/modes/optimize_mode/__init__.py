import os
from multiprocessing import cpu_count
from typing import Dict, List
import arrow
import click
import jesse.helpers as jh
from jesse.modes.backtest_mode import load_candles
from jesse.services.validators import validate_routes
from jesse.store import store
from .Optimize import Optimizer
from jesse.services.failure import register_custom_exception_handler
from jesse.routes import router

os.environ['NUMEXPR_MAX_THREADS'] = str(cpu_count())


def run(
        debug_mode,
        user_config: dict,
        routes: List[Dict[str, str]],
        extra_routes: List[Dict[str, str]],
        start_date: str,
        finish_date: str,
        optimal_total: int,
        csv: bool