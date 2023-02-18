from jesse.config import config
from jesse.enums import exchanges, timeframes
from jesse.routes import router
from jesse.store import store


def test_routes():
    # re-define routes
    router.set_routes([
        {'exchange': exchanges.BITFINEX_SPOT, 'symbol': 'ETH-USD', 'timeframe': timeframes.HOUR_3, 'strateg