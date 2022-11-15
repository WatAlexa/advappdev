import numpy as np

import jesse.helpers as jh
from jesse.services import selectors
from jesse.libs import DynamicNumpyArray
from jesse.models import store_orderbook_into_db


class OrderbookState:
    def __init__(self) -> None:
        self.storage = {}
        self.temp_storage = {}

    def init_storage(self) -> None:
        for ar in selectors.get_all_routes():
            exchange, symbol = ar['exchange'], ar['symbol']
            key = jh.key(exchange, symbol)
            self.temp_storage[key] = {
                'last_updated_timestamp': None,
                'asks': [],
                'bids': []
            }
        