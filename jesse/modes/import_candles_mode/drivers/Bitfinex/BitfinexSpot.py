import requests

import jesse.helpers as jh
from jesse import exceptions
from jesse.modes.import_candles_mode.drivers.interface import CandleExchange
from jesse.enums import exchanges
from .bitfinex_utils import timeframe_to_interval


class BitfinexSpot(CandleExchange):
    def __init__(self) -> None:
        super().__init__(
            name=exchanges.BITFINEX_SPOT,
            count=1440,
            rate_limit_per_second=1,
            backup_exchange_class=None
        )

        self.endpoint = 'https://api-pub.bitfinex.com/v2/candles'

    def get_starting_time(self, symbol: str) -> int:
        dashless_symbol = jh.dashless_symbol(symbol)

        # hard-code few common symbols
        if symbol == 'BTC-USD':
            return jh.date_to_timestamp('2015-08-01')
        elif symbol ==