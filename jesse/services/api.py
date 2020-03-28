import threading
from typing import Union

import jesse.helpers as jh
from jesse.models import Order
from jesse.services import logger


class API:
    def __init__(self) -> None:
        self.drivers = {}

        if not jh.is_live():
            self.initiate_drivers()

    def initiate_drivers(self) -> None:
        considering_exchanges = jh.get_config('app.considering_exchanges')

        # A helpful assertion
        if not len(considering_exchanges):
            raise Exception('No exchange is available for initiating in the API class')

        for e in considering_exchanges:
            if jh.is_live():
                def initiate_ws(exchange_name: str) 