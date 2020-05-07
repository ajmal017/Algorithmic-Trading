#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  4 16:03:47 2020

@author: josephgross
"""


import datetime
import pprint
try:
    import Queue as queue
except ImportError:
    import queue
    
import time

class Backtest(object):
    """
    Encapsulates the setting and components for carrying out
    an event-driven backtest.
    
    
    This object encapsulates the event-handling logic and it
    essentially ties together all of the other classes.
    
    This object is designed to carry out a nested while-loop
    event-driven system in order to handle the events placed
    on the Event Queue object. The outer while-loop is known
    as the "heartbeat loop" and decides the temporal resolution
    of the backtesting-system. In a live environment, the value 
    will be a positive number, such as 600 seconds (10 minutes).
    Thus, the market data and positions will only be updated on 
    this timeframe.
    
    For a backtester, this heartbeat can be set to 0 becuase all
    the historical data is already avaialble.
    
    The inner while loop processes the signals and sends them to 
    the correct component depending upon the event. Thus, the 
    Event Queue is continaully being populated and depopulated with
    events.
    """
    
    def __init__(
            self, csv_dir, symbol_list, initial_capital, 
            heartbeat, start_date, data_handler, 
            execution_handler, portfolio, strategy
            ):
        """
        

        Parameters
        ----------
        csv_dir : 'str'
            The hard root to the CSV data directory.
        symbol_list : 'list'
            The list of symbol strings.
        initial_capital : 'float'
            The starting capital for the portfolio.
        heartbeat : 'int'
            Backtest "heartbeat" in seconds.
        start_date : 'datetime'
            The start datetime of the strategy.
        data_handler : 'DataHandler'
            Handles the market data feed.
        execution_handler : 'ExecutionHandler'
            Handles the orders/fills for trades.
        portfolio : 'Portfolio'
            Keeps track of portfolio current and prior positions.
        strategy : 'Strategy'
            Generates signals based on market data.

        Returns
        -------
        None.

        """
        
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        
        self.data_handler_cls = data_handler
        self.execution_handler_cls = execution_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy
        
        self.events = queue.Queue()
        
        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strates = 1
        
        self._generate_trading_instances()
        
        
    def _generate_trading_instances(self, strategy_params_dict):
        """
        Generates the trading instance objects from their class types.

        Returns
        -------
        None.

        """
        
        print(
            "Creating DataHandler, Strategy, Portfolio, and ExecutionHandler"
        )
        
        self.data_handler = self.data_handler_cls(self.events, self.csv_dir, 
                                                  self.symbol_list)
        self.strategy = self.strategy_cls(self.data_handler, self.events, **strategy_params_dict)
        self.portfolio = self.portfolio_cls(self.data_handler, self.events,
                                            self.start_date, 
                                            self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.events)
        
        
    def _run_backtest(self):
        """
        Executes the backtest.
        
        This method is where the signal handling of the Backtest engine
        is carried out. For a MarketEvent,the Strategy object is told to
        recalculate new signals, while the Portfolio is told to reindex
        the time. If a SignalEvent object is received, the Portfolio is 
        told to handle the new signal and convert it into a set of OrderEvents.
        If an OrderEvent is received, the ExecutionHandler is sent the order
        to be transmitted to the broker (if in a real live trading setting).
        Finally, if a FillEvent is received, the Portfolio will update itself
        to be aware of the new positions.
        

        Returns
        -------
        None.

        """
        
        i = 0
        while True:
            i += 1
            print(i)
            # Update the market bars
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()
            else:
                break
            
            # Handle the events
            while True:
                try: 
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                            
                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(event)
                            
                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)
                            
                        elif event.type == 'FILL':
                            self.fills ++ 1
                            self.portfolio.update_fill(event)
                            
            time.sleep(self.heartbeat)
            
            
    def _output_performance(self):
        """
        Outputs the strategy performance from the backtest.

        Returns
        -------
        None.

        """
        
        self.portfolio.create_equity_curve_dataframe()
        
        print("Creating summary stats...")
        stats = self.portfolio.output_summary_stats()
        
        print("Creating equity curve...")
        print(self.portfolio.equity_curve.tail(10))
        pprint.pprint(stats)
        
        print("Signals: %s" % self.signals)
        print("Orders: %s" % self.orders)
        print("Fills: %s" % self.fills)
    
        
    def simulate_trading(self):
        """
        Simulates the backtest and outputs portfolio performance.
        
        This method simply calls the two previous methods.

        Returns
        -------
        None.

        """
        
        self._run_backtest()
        self._output_performance()
        
        