from jesse.strategies import Strategy
import jesse.helpers as jh
from jesse import utils


class TestCanSubmitTakeProfitAndStopLossAtSameTimeInSpot(Strategy):
    def should_long(self):
        return self.price in [10, 20]

    def go_long(self):
        if self.price == 10:
            self.buy = 1, self.price
        elif self.price == 20:
            self.buy = 2, self.price

    def on_open_position(self, order) -> None:
        if self.price == 10:
            self.take_profit = self.position.qty, 15
            self.stop_l