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

    start_date = datetime.fromtimestamp(store.app.starting_time / 10