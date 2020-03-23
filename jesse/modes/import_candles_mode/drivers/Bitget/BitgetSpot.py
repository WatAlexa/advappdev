from typing import Union
import requests
from jesse.modes.import_candles_mode.drivers.interface import CandleExchange
from .bitget_spot_utils import timeframe_to_interval
import jesse.helpers as jh
from jesse.enums import exchanges
from jesse import exceptions


class BitgetSpot(CandleExchange):
    def __init__(self) -> None:
        super().__init__(
            name=exchanges.BITGET_SPOT,
            count=100,
            rate_limit_per_second=18,
            backup_exchange_class=None
        )

        self.endpoint = 'https://api.bitget.com/api/spot/v1/market/candles'

    def get_starting_time(self, symbol: str) -> int:
        payload = {
            'after': 1359291660000,
            'before': jh.now(force_fresh=True),
            'period': '1week',
            'symbol': self._jesse_symbol_to_bitget_usdt_contracts_symbol(symbol),
        }

        response = requests.get(self.endpoint, params=payload)

        self.validate_bitget_response(response)

        data = response.json()

        # since the first timestamp doesn't include all the 1m
        # candles, let's start since the second day then
        return int(data[1][0])

    def fetch(self, symbol: str, start_timestamp: int, timeframe: str = '1m') -> Union[list, None]:
        end_timestamp = start_timestamp + (self.count - 1) * 60000 * jh.timeframe_to_one_minutes(timeframe)

        payload = {
            'period': timeframe_t