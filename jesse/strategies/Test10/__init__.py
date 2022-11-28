from jesse.strategies import Strategy


# test_taking_profit_at_multiple_points
class Test10(Strategy):
    def should_long(self):
        return self.price < 7

    def should_short(self):
        return False

    def go_long(self):
        qty = 1.5
        self.buy = qty, 7
        self.stop_loss = qty, 5
        self.take_profit = [
       