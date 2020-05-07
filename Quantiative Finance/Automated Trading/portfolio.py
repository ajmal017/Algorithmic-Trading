#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 10:34:01 2020

@author: josephgross
"""


import datetime
from math import floor
try:
    import Queue as queue
except ImportError:
    import queue
    
import numpy as np
import pandas as pd

from event import FillEvent, OrderEvent
from performance import create_sharpe_ratio, create_drawdowns


class Portfolio(object):
    """
    The Portfolio class handles the positions and market value
    of all instruments at a resolution of a "bar",
    i.e. secondly, minutely, 5-min, 30-min, 60-min, or EOD.
    
    The positions DataFrame stores a time-index of the quantity
    of positions held.
    
    The holdings DataFrame stores the cash and total market holdings
    value of each symbol for a particular time-index, as well as the
    percentage change in portfolio total across bars.
    
    The Portfolio class keeps track of all the positons within a 
    portfolio and generates orders of a fixed quantity of stock based
    on signals. More sophisticated portfolio objects include risk 
    mangaement and position sizing tools (such as the Keylly Criterion).
    
    The portfolio is the most complex component of an event_driven 
    backtester. In additon to the positions and holdings management, 
    the portfolio must be aware of risk factors and position sizing
    techniques in order to optimize orders that are sent to a brokerage
    or other forms of market access.
    
    NOTE:
        This potfolio object generates 'dumb' orders and does not take
        into account risk management. 
        
    FUTURE IMPROVEMENTS:
        - Replace generate_naive_order with a risk management method
          that takes into account the n% rule (normally 1%-3%).
        - Figure out a way to incoporate stop-loss orders 
            - Maybe add functionality to the portfolio to excecute a
              'Sell' FillEvent Object once the price passes a certain 
              point.
        
    
    """
    
    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        """
        Initializes the portfolio with bars and an event queue. Also 
        includes a starting datetime index and initial capital (which 
        USD unless stated otherwise).

        Parameters
        ----------
        bars : 'DataHandler'
            The DataHandler object with current market data.
        events : 'Queue'
            The Event Queue object.
        start_date : 'datetime'
            the start date (bar) of the portfolio.
        initial_capital : 'float', optional
            The starting capital in USD. The default is 100000.0.

        Returns
        -------
        None.

        """
        
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital
        
        self.all_positions = self.construct_all_positions()
        self.current_positions = dict( (k,v) for k, v in 
                                      [(s, 0) for s in self.symbol_list] )
        
        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()
        
    
    def construct_all_positions(self):
        """
        Constructs the positions list using the start_date to 
        determine when the time index will begin.
        
        Creates a dictionary for each symbol, sets the value to 
        zero for each, and then adds a datetime key, finally adding
        it to a list.

        Returns
        -------
        None.

        """
        
        d = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        d['datetime'] = self.start_date
        return [d]
    
    
    def construct_all_holdings(self):
        """
        Constructs the holdings list using the start_datea to determing
        when the time index will begin.
        
        Creates a dictionary for each symbol, sets the value to 
        zero for each, and then adds a datetime key, finally adding
        it to a list. Also inludes extra keys for cash, commission, and
        total, which respectively represent the spare cash in the account
        after any purchases,the cumulative commission accrued and the total 
        account equity inlcuding cash and any open positions.
        
        Short positions are treated as negative. The starting cash and 
        total account equity are both set to the initia capital.

        Returns
        -------
        None.

        """
        
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]
    
    
    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the instantaneous
        value of the portfolio across all symbols.

        Returns
        -------
        None.

        """
        
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d
    
    
    
    def update_timeindex(self, event):
        """
        Adds a new record to the positions matrix for the current market
        data bar. This reflects the PREVIOUS bar, i.e. all current market
        data at this stage is known (OHLCV).
        
        This method handles the new holdings tracker. It firstly obtains 
        the latest prices from the market data handler and creates a new
        dictionary of symbols to represent current postions, by setting 
        the "new" positions equal to the "current" positions. The current 
        positions are only modified when a FillEvent is obtained. The method
        then appends this set of current positions to the all_positions list.
        
        Makes use of a MarketEvents fom the events queue

        Parameters
        ----------
        event : Event
            The event to be handled (i.e. FillEvent)


        Returns
        -------
        None.

        """
        
        latest_datetime = self.bars.get_latest_bar_datetime(self.symbol_list[0])
        
        # Update positions
        # ================
        dp = dict( (k,v) for k, v in [(s,0) for s in self.symbol_list] )
        dp['datetime'] = latest_datetime
        
        for s in self.symbol_list:
            dp[s] = self.current_positions[s]
            
        # Append the current positions
        self.all_positions.append(dp)
        
        
        # Update holdings
        # ================
        dh = dict( (k,v) for k, v in [(s,0) for s in self.symbol_list] )
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']
        
        for s in self.symbol_list:
            # Approximation to the real value
            market_value = self.current_positions[s] * \
                self.bars.get_latest_bar_value(s, "adj_close")
            dh[s] = market_value
            dh['total'] += market_value
            
        
        # Append the current holdings
        self.all_holdings.append(dh)
        
        
        
    def update_positions_from_fill(self, fill):
        """
        Takes a Fill object and updates the positions matrix to reflect
        the new positions.
        
        Determines whether the FillEvent is a 'Buy' or a 'Sell' and then
        updates the current_positions dictionary accordinly by adding or
        subtracting.

        Parameters
        ----------
        fill : 'Event'
            The FillEvent object to update the position with.

        Returns
        -------
        None.

        """
        
        # Check whethere the fill is a buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1
            
        # Update positions list with new quantities
        self.current_positions[fill.symbol] += fill_dir * fill.quantity
        
        
    def update_holdings_from_fill(self, fill):
        """
        Takes a Fill object and updates the holdings matrix to reflect
        the holdings values.
        
        Similar to update_positions_from_fill method but updates the
        holdings values instead. In order to simulate the cost of fill, 
        this method does not use the associated cost from the FillEvent. 
        Instead, the fill cost is set to the "current maket price" which 
        is the closing price of the last bar. The holdings for a particular
        symbol are then set to be equal to the fill cost multiplied by the 
        transacted quantity. 

        Parameters
        ----------
        fill : 'Event'
            The FillEvent object to update the position with.

        Returns
        -------
        None.

        """
        
        # Check whethere the fill is a buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1
            
        # Update holdings list with new quantities
        fill_cost = self.bars.get_latest_bar_value(fill.symbol, "adj_close")
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)
        
        
    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings from a 
        FillEvent.
        
        This method simply executs the two previous methods:
            update_positions_from_fill and update_holdings_from_fill
        upon receipt of a fill event

        Parameters
        ----------
        event : 'Event'
            The Event object to update the portfolio with.

        Returns
        -------
        None.

        """
        
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)
            
            
            
    def generate_naive_order(self, signal):
        """
        Simply files an Order object as a constant quantity sizing
        of the signal object, without risk management or position 
        sizing considerations. 
        
        This method takes a signal to go long or short an asset, 
        sending an order to do so for 100 shares of such an asset. 
        
        In realistic implementation, this value (100) will be determined
        by a risk management of position sizing overlay. 
        
        This method handles longing, shorting, and exiting of a position, 
        based on the current quantity and particular symbol. Corresponding
        OrderEvent objects are then generated.


        Parameters
        ----------
        signal : 'tuple'
            The tuple containing Signal information.

        Returns
        -------
        'Event'
            Returns an OrderEvent to be filled

        """
        
        order = None
        
        symbol = signal.symbol
        direction = signal.signal_type
        strength = signal.strength
        
        mkt_quantity = 100
        cur_quantity = self.current_positions[symbol]
        order_type = 'MKT'
        
        if direction == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        if direction == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')
            
            
        if direction == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        if direction == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')
            
        return order
    
    
    def update_signal(self, event):
        """
        Acts on SignalEvent to generate new orders based on the portfolio 
        logic.
        
        This method simply calls the 'generate_naive_order' method and 
        adds the generated order to the events queue.

        Parameters
        ----------
        event : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)
            
            
            
    def create_equity_curve_dataframe(self):
        """
        Creates a Pandas DataFrame from the all_holdings list
        of dictionaries.
        
        This method creates a returns stream, and then normalises the
        equity curve to be percentage based. Thus the account initial
        size is equal to 1.0, as opposed to the absolute dollar amount.
        """
        
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        self.equity_curve = curve
        
        
    def output_summary_stats(self):
        """
        Creates a list of summary statistics for the portfolio
        
        This method outputs the equity curve and varioys performance 
        statistics related to the strategy. 
        
        The final line ouputs a file, equity.csv, to the same directory
        as the code, whcih can be loaded into a Matplotlib Python script
        for subsequent analysis.
        
        Note:
            The drawdown duration is given in terms of the absolute 
            number of "bars" that teh drawdown carried on for, as 
            opposed to a particular timeframe.

        Returns
        -------
        'list'
            Returns a list of stats relating to portfolio performance

        """
        
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']
        
        sharpe_ratio = create_sharpe_ratio(returns, periods=252) # For Minute level bars: periods=252*6.5*60
        drawdown, max_dd, dd_duration = create_drawdowns(pnl)
        self.equity_curve['drawdown'] = drawdown
        
        stats = [("Total Return", "%0.2f%%" % ((total_return-1)*100.0)),
                  ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
                   ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)),
                   ("Drawdown Duration", "%d" % dd_duration)]
        
        self.equity_curve.to_csv('equity.csv')
        return stats