import datetime

from executionhandlers.execution_handler import ExecutionHandler
from events.fill_event import FillEvent
from events.order_event import OrderEvent
from oanda.order_api_client import OrderApiClient
from oanda.trade_api_client import TradeApiClient
from loggers.logger import Logger
from typing import Dict
from datahandlers.data_handler import DataHandler

try:
    import Queue as queue
except ImportError:
    import queue


class OandaExecutionHandler(ExecutionHandler):
    def __init__(self, bars: DataHandler, events_per_symbol: Dict[str, queue.Queue],
                 account_id: str, access_token: str, logger: Logger):
        self.bars = bars
        self.events_per_symbol = events_per_symbol
        self.access_token = access_token
        self.account_id = account_id
        self.logger = logger

        self.limit_and_stop_orders = list()

    def execute_order(self, event):
        """
        :type event: OrderEvent
        """
        if event.type == 'ORDER':
            order_api = OrderApiClient(self.account_id, self.access_token)
            trade_api = TradeApiClient(self.account_id, self.access_token)

            if event.order_type == 'MKT':

                if event.direction == 'EXIT':
                    response = trade_api.close_trade(event.trade_id_related_to)
                else:
                    response = order_api.create_new_order(event.direction, event.quantity, event.symbol,
                                                          event.stop_loss, event.take_profit)

                if 'errorCode' in response or 'errorMessage' in response:
                    error_message = response['errorMessage']

                    if 'errorCode' in response:
                        error_code = response['errorCode']
                    else:
                        error_code = ''

                    # intentionally - when trade is closed by broker (it's already filled, we need to simulate fill)
                    if error_code == 'TRADE_DOESNT_EXIST' and event.direction == 'EXIT':
                        fill_event = FillEvent(
                            datetime.datetime.utcnow(), event.symbol, 'FOREX', event.quantity, event.direction, None,
                            None, 0
                        )

                        self.events_per_symbol[fill_event.symbol].put(fill_event)

                    self.logger.write(
                        'Error during executing the order: errorCode=%s, errorMessage="%s"' % (
                            error_code, error_message))
                else:
                    if 'tradeOpened' in response['orderFillTransaction']:
                        trade_id = int(response['orderFillTransaction']['tradeOpened']['tradeID'])
                    else:
                        trade_id = 0

                    fill_event = FillEvent(
                        datetime.datetime.utcnow(), event.symbol, 'FOREX', event.quantity, event.direction, None, None,
                        trade_id
                    )

                    if event.stop_loss is not None:
                        stop_loss = event.stop_loss
                    else:
                        stop_loss = 0.0

                    if event.take_profit is not None:
                        take_profit = event.take_profit
                    else:
                        take_profit = 0.0

                    self.logger.write(
                        'Executed the order with stopLoss=%10.5f, takeProfit=%10.5f' % (
                            stop_loss, take_profit))

                    self.events_per_symbol[fill_event.symbol].put(fill_event)

    def update_stop_and_limit_orders(self, market_event):
        pass

    def clear_limit_or_stop_orders(self, close_pending_orders_event):
        pass
