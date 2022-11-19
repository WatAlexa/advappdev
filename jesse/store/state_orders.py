from typing import List

import pydash

from jesse.config import config
from jesse.models import Order
from jesse.services import selectors
import jesse.helpers as jh


class OrdersState:
    def __init__(self) -> None:
        # used in simulation only
        self.to_execute = []

        self.storage = {}

        for exchange in config['app']['trading_exchanges']:
            for symbol in config['app']['trading_symbols']:
                key = f'{exchange}-{symbol}'
                self.storage[key] = []

    def reset(self) -> None:
        """
        used for testing
        """
        for key in self.storage:
            self.storage[key].clear()

    def reset_trade_orders(self, exchange: str, symbol: str) -> None:
        """
        used after each completed trade
        """
        key = f'{exchange}-{symbol}'
        self.storage[key] = []

    def add_order(self, order: Order) -> None:
        key = f'{order.exchange}-{order.symbol}'
        self.storage[key].append(order)

    def remove_order(self, order: Order) -> None:
        key = f'{order.exchange}-{order.symbol}'
        self.storage[key] = [
            o for o in self.storage[key] if o.id != order.id
        ]

    def execute_pendi