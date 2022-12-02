from jesse.strategies import Strategy


# test_on_route_open_position part 1 - BTC-USD
class Test21(Strategy):
    def should_long(self):
        # buy on m