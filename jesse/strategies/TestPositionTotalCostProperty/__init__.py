from jesse.strategies import Strategy
import jesse.helpers as jh
from jesse import utils


class TestPositionTotalCostProperty(Strategy):
    def before(self) -> None:
        if self.price == 20:
            if self.exchange_type == 'futures':
                assert self.posi