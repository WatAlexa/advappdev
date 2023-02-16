from jesse.enums import exchanges
from jesse.models import Position
from jesse.testing_utils import set_up, single_route_backtest


def test_close_position():
    set_up()

    p = Position(exchanges.SANDBOX, 'BTC-USDT', {
        'entry_price': 50,
        'current_price': 50,
        'qty': 2,
    })
    assert p.exit_price is None

    p._mutating_close(50)

    assert p.qty == 0
    assert p.entry_price is None
    assert p.exit_price == 50


def test_increase_a_long_position():
    set_up()

    p = Position(exchanges.SANDBOX, 'BTC-USDT', {
        'entry_price': 50,
        'current_price': 50,
        'qty': 2,
    })

    p._mutating_increase(2, 100)

    assert p.qty == 4
    assert p.entry_price == 75


def test_increase_a_short_position():
    set_up()

    p = Position(exchanges.SANDBOX, 'BTC-USDT', {
        'entry_price': 50,
        'current_price': 50,
        'qty': -2,
    })

    p._mutating_increase(2, 40)

    assert p.qty == -4
    assert p.entry_price == 45


def test_initiating_position():
    position = Position(exchanges.SANDBOX, 'BTC-USDT', {
        'current_price': 100,
        'qty': 0
    })

    assert position.exchange_name == 'Sandbox'
    assert position.symbol == 'BTC-USDT'
    assert position.current_price == 100
    assert position.qty == 0
    assert position.closed_at is Non