
from jesse.strategies import Strategy


# test_shared_vars [part 1]
class Test32(Strategy):
    def __init__(self) -> None:
        super().__init__()

        self.shared_vars['buy-eth'] = False

    def before(self):
        if self.index == 10:
            self.shared_vars['buy-eth'] = True

    def should_long(self):
        return False
