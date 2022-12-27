from jesse.strategies import Strategy
import jesse.helpers as jh
from jesse import utils


class TestDailyBalanceStoresPortfolioValue(Strategy):
    def before(self) -> None:
        if self.index == 0:
            assert self.balance == 10_000

        if self.price == 11:
            assert self.portfolio_value == 10_000
            if self.is_spot_trading:
                assert self.balance == 10_000 - (50 * 9)

    def should_long(self) -> bool:
        return self.price == 10

    def go_long(self) -> None:
        # submit an entry buy order that is not supposed to be filled
        self.buy = 50, 9

    def should_can