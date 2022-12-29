from jesse.strategies import Strategy


class TestMarketOrderForLowPriceDifference(Strategy):
    def on_open_position(