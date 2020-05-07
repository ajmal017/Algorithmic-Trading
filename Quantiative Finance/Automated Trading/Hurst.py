#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 11 18:43:21 2020

@author: josephgross
"""


# H < 0.5 - The time series is mean reverting (near 0 means highly mean reverting)
# H = 0.5 - The time series is a Geometric Brownian Motion
# H < 0.5 - The time seris is trending (near 1 means strongly trending)

import datetime as dt
from alpha_vantage.timeseries import TimeSeries
import pandas as pd

from numpy import array, cumsum, log, polyfit, sqrt, std, subtract
from numpy.random import randn


def hurst(time_series):
    """
    Calculates the Hurst Exponent of the time series vector ts

    Parameters
    ----------
    time_series : 'np,darray'
        Time series array of prices

    Returns
    -------
    'float'
        The Hurst Exponential of the time series

    """
    
    # Create the range of lag values
    lags = range(2, 100)
    
    # Calculate the array of the variances of the lagged differences
    tau = [
        sqrt(std(subtract(time_series[lag:], time_series[:-lag])))
        for lag in lags
    ]
    
    # Use a linear fit to estimate the Hurst Exponent
    poly = polyfit(log(lags), log(tau), 1)
    
    # Return the Hurst Exponent from the polyfit output
    return poly[0] * 2.0

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


# ==================================================================


if __name__ == "__main__":
    
    # Create a Gometric Brownian Motion, Mean-Reverting and Trending Series
    gbm = log(cumsum(randn(100000)) + 1000)
    mr = log(randn(100000) + 1000)
    tr = log(cumsum(randn(100000) + 1) + 1000)
    
    # Download the Amazon OHLCV data 
    start_date = dt.datetime(2000, 1, 1)
    end_date = dt.datetime(2015, 1, 1)
    amzn = get_daily_historic_data_alphavantage('AMZN', start_date, end_date)
    
    # Output the Hurst Exponent for each of the above series
    # and the price of Amazon (the Adjusted Close Price) for
    # the ADF test given above in the article
    print("Hurst (GBM):    %0.2f" % hurst(gbm))
    print("Hurst (MR):    %0.2f" % hurst(mr))
    print("Hurst (TR):    %0.2f" % hurst(tr))
    
    # Calculate the Hurst exponent for the AMZN adjusted closing prices
    print("Hurst (AMZN):    %0.2f" % hurst(array(amzn['Adj Close'].tolist())))
    
    
    