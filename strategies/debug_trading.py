from __future__ import print_function

import datetime
from events.signal_event import SignalEvent
from strategies.strategy import Strategy
import argparser_tools.basic
from typing import Dict
from datahandlers.data_handler import DataHandler
from core.portfolio import Portfolio

try:
    import Queue as queue
except ImportError:
    import queue


class DebugTradingStrategy(Strategy):
    def __init__(self, bars: DataHandler, portfolio: Portfolio, events_per_symbol: Dict[str, queue.Queue],
                 signal_file: str, stop_loss_pips=None, take_profit_pips=None):

        self.bars = bars
        self.portfolio = portfolio
        self.symbol_list = self.bars.get_symbol_list()
        self.events_per_symbol = events_per_symbol
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_pips = take_profit_pips
        self.signal_file = signal_file

        # Set to True if a symbol is in the market
        self.bought = self._calculate_initial_bought()

        self.signal_file_opened = open(self.signal_file, 'r')

        self.force_new_signal_type = None

    def _calculate_initial_bought(self):
        """
        Adds keys to the bought dictionary for all symbols
        and sets them to 'OUT'.
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'

        return bought

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            symbol = event.symbol

            if not self.bars.has_some_bars(symbol):
                return

            if self.portfolio.current_positions[symbol] == 0:
                self.bought[symbol] = 'OUT'

            bar_date = self.bars.get_latest_bar_datetime(symbol)
            bar_price = self.bars.get_latest_bar_value(symbol, 'close_bid')

            dt = datetime.datetime.utcnow()

            self.signal_file_opened.seek(0, 0)
            signal_from_file = self.signal_file_opened.readline()

            long_signal = signal_from_file == 'long'
            short_signal = signal_from_file == 'short'
            exit_signal = signal_from_file == 'exit'

            signal_generated = self.calculate_exit_signals(short_signal, long_signal, exit_signal, symbol, bar_date,
                                                           dt)

            if signal_generated is False:
                self.calculate_new_signals(short_signal, long_signal, symbol, bar_date, bar_price, dt)

    def calculate_new_signals(self, short_signal, long_signal, symbol, bar_date, bar_price, dt):

        current_position = self.portfolio.get_current_position(symbol)

        if long_signal and current_position is None:
            sig_dir = 'LONG'

            stop_loss = self.calculate_stop_loss_price(bar_price, self.stop_loss_pips, sig_dir)
            take_profit = self.calculate_take_profit_price(bar_price, self.take_profit_pips, sig_dir)

            signal = SignalEvent(1, symbol, bar_date, dt, sig_dir, 1.0, stop_loss, take_profit)
            self.events_per_symbol[symbol].put(signal)
            self.bought[symbol] = sig_dir

            return True

        elif short_signal and current_position is None:
            sig_dir = 'SHORT'

            stop_loss = self.calculate_stop_loss_price(bar_price, self.stop_loss_pips, sig_dir)
            take_profit = self.calculate_take_profit_price(bar_price, self.take_profit_pips, sig_dir)

            signal = SignalEvent(1, symbol, bar_date, dt, sig_dir, 1.0, stop_loss, take_profit)
            self.events_per_symbol[symbol].put(signal)
            self.bought[symbol] = sig_dir

            return True

        return False

    def calculate_exit_signals(self, short_signal, long_signal, exit_signal, symbol, bar_date, dt):

        current_position = self.portfolio.get_current_position(symbol)

        if current_position is not None and (
                (current_position.is_long() and short_signal) or
                (current_position.is_short() and long_signal) or exit_signal):
            sig_dir = 'EXIT'

            signal = SignalEvent(1, symbol, bar_date, dt, sig_dir, 1.0, None, None, current_position.get_trade_id())
            self.events_per_symbol[symbol].put(signal)

            self.bought[symbol] = 'OUT'

            return True

        return False

    @staticmethod
    def get_strategy_params(args_namespace):
        return dict(signal_file=args_namespace.signal_file)

    @staticmethod
    def create_argument_parser(backtest_only):
        # () -> argparse.ArgumentParser

        parser = argparser_tools.basic.create_basic_argument_parser(backtest_only)

        if (backtest_only):
            parser = argparser_tools.basic.with_backtest_arguments(parser)

        parser.add_argument('--signal_file', type=argparser_tools.basic.existing_file)

        return parser
