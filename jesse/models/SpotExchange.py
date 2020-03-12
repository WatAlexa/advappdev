import jesse.helpers as jh
from jesse.enums import sides
from jesse.exceptions import InsufficientBalance
from jesse.models import Order
from jesse.models.Exchange import Exchange
from jesse.enums import order_types
from jesse.utils import sum_floats, subtract_floats


class SpotExchange(Exchange):
    def __init__(self, name: str, starting_balance: float, fee_rate: float):
        super().__init__(name, starting_balance, fee_rate, 'spot')

        self.stop_orders_sum = {}
        self.limit_orders_sum = {}

        # # # # live-trading only # # # #
        self._started_balance = 0
        # # # # # # # # # # # # # # # # #

    @property
    def started_balance(self) -> float:
        if jh.is_livetrading():
            return self._started_balance

        return self.starting_assets[jh.app_currency()]

    @property
    def wallet_balance(self) -> 