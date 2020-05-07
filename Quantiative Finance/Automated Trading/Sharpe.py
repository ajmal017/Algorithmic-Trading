#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 21:25:43 2020

@author: josephgross
"""


# Sharpe RAtio
# The Sharpe ratio helps compare two strategies with identical returns
# by taking into account the volatility of returns and periods of drawdown

# The Sharpe Ratio often quotes by those carrying out trading strategies is the
# annualized sharpe, the calculation of which depends upon the trading period of 
# which the returns are measure

# The Sharpe ratio must be calulated upon the tradin gperiod of which the returns
# are measured. For a strategy based of trading perood of days, N=252 (trading days 
# in a year) and Ra and Rb must be the daily returns. For hours, N = 252 x 6.5 = 1638.

# The formula for the Sharpe ratio alludes to the use of a benchmark which is used as 
# "hurdle" that a particular strategy must overcome for it to be worth consideration.
# Example: a simple long-only strategy using US large-cap equities should hope to beat
# the S&P500 index on average or match  it for less volatility.

# Transactio costs MUST be in included in order for the Sharpe ratio to be realistic

# What is a good Sharpe Ratio?
# S < 1 should not be considered a good strategy
# Most quant funds use the threshold S < 2
# As a retail trader, if you can achive a Sharpe Ratio of
# S > 2, then you are doing very well


import datetime as dt
from alpha_vantage.timeseries import TimeSeries

import numpy as np
import pandas as pd



def get_daily_historic_data_alphavantage(ticker, start_date, end_date):
    """
    
    Use the generated API call to query AlphaVantage with the 
    appropriate API key and return a list of price tuples for 
    a particular ticker

    Parameters
    ----------
    ticker : 'str'
        The ticker of a stock which will be used to retrieve price data
        from alpha_vantage

    Returns
    -------
    'list'
        List of tuples with historical price data based on a 
        specific ticker
    """
    
    ALPHA_VANTAGE_API_KEY = 'YZZ4PFN9ATU1ASPAN'
    COLUMNS = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
    
    try:
        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='json')
        data, meta_data = ts.get_daily_adjusted(symbol=ticker, outputsize='full')
    except Exception as e:
        print(
            "Could not download AlphaVantage data for %s ticker "
            "(%s)...skipping." % (ticker, e)
            )
        return []
    else:
        prices = []
        
        for date_str in sorted(data.keys()):
            date = dt.datetime.strptime(date_str, '%Y-%m-%d') 
            if date < start_date or date > end_date:
                continue
            
            bar = data[date_str]
            prices.append(
                (
                    date_str,
                    float(bar['1. open']),
                    float(bar['2. high']),
                    float(bar['3. low']),
                    float(bar['4. close']),
                    int(bar['6. volume']),
                    float(bar['5. adjusted close'])
                    )
                )

    return pd.DataFrame(prices, columns=COLUMNS).set_index('Date')
    

def annualised_sharpe(returns, N=252):
    """
    Calculate the annualised Sharpe ratio o fa returns stream
    based on a number of trading periods, N. N defaults to 252, 
    which then assums a stream of daily returns
    
    The function assumes that the returns are the excess of those 
    compared to a benchmark

    Parameters
    ----------
    returns : 'pd.DataFrame'
        DataFrame of daily returns
    N : 'int', optional
        The number of trading periods upon which the ratio is
        based on. The default is 252.

    Returns
    -------
    None.

    """
    
    return np.sqrt(N) * returns.mean() / returns.std()


def equity_sharpe(ticker):
    """
    Calculates the annualised Sharpe ratio based on the daily
    returns of an equity ticker symbol listed in AlphaVantage

    Parameters
    ----------
    ticker : 'pd.DataFrame'
        DataFrame that contains the return info for an equity
        ticker symbol whose equity sharpe ratio is desired

    Returns
    -------
    'int'
        Equity Sharpe Ratio

    """
    
    # Use the percentage change method to easily calculate daily returns
    ticker['daily_ret'] = ticker['Close' ].pct_change()
    
    # Assume an average annual risk-free rate over the period of 5%
    ticker['excess_daily_ret'] = ticker['daily_ret'] - 0.05/252
    
    return annualised_sharpe(ticker['excess_daily_ret'])


def market_neutral_sharpe(ticker, benchmark):
    """
    Calculates the annualised Sharpe ratio of a market neutral
    long/short strategy inbolbing the long og 'ticker' with a 
    corresponding short of the 'benchmark'

    Parameters
    ----------
    ticker : 'pd.DataFrame'
        OHLCV data for the ticker
    benchmark : 'pd.DataFrame'
        OHLCV data for the benchmark instrument

    Returns
    -------
    'float'
        Market Neutral Sharpe Ratio

    """
    
    # Calculate the percentage returns on each of the time series
    ticker['daily_ret'] = ticker['Close'].pct_change()
    benchmark['daily_ret'] = benchmark['Close'].pct_change()
    
    # Create a new DataFrame to store the strategy information
    # The net returns are (long - short)/2, since there is twice 
    # the trading capita; for this strategy
    strat = pd.DataFrame(index=ticker.index)
    strat['net_ret'] = (ticker['daily_ret'] - benchmark['daily_ret'])/2.0
    
    # Return the annualised Sharpe ratio for this strategy
    return annualised_sharpe(strat['net_ret'])
    

# ================================================


if __name__ == "__main__":
    
    # Download the Alphabet (Google) OHLCV data from 1/1/2005 to 1/1/2013
    start_date = dt.datetime(2005, 1, 1)
    end_date = dt.datetime(2013, 1, 1)
    
    
    # Create a DataFramae of Google stock prices
    goog = get_daily_historic_data_alphavantage('GOOGL', start_date, end_date)
    
    # Create a DataFrame of S&P ETF stock prices based on AlphaVantage data
    spy = get_daily_historic_data_alphavantage('SPY', start_date, end_date)
    
        
  
    print (
        "AlphaBet Sharpe Ratio: %s" %
        equity_sharpe(goog)
    )
    
    print (
        "AlphaBet Market Neutral Sharpe Ratio: %s" %
        market_neutral_sharpe(goog, spy)
    )
    