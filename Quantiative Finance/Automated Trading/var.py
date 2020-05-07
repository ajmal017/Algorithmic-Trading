#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 18:43:29 2020

@author: josephgross
"""


# Value at Risk, or VaR estimates the risk of loss to an algorithmic trading strategy.
# VaR provides an estimate, under a given degree of confidence, of the size of a loss 
# from a portfolio over a given time peiod.

# Example:
# A VaR equal to 500,000 USD at a 95% confidence level for a time period of a day would
# simply state that there is a 95% probability of losing no more than 500,000 USD in the 
# following day


import datetime as dt

import numpy as np
from scipy.stats import norm
import pandas as pd

from alpha_vantage.timeseries import TimeSeries


def get_daily_historic_data(ticker, start_date, end_date):
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


def var_cov_var(P, c, mu, sigma):
    """
    Variance-Covariance calculation of daily Value-at-Risk using confidence 
    level c, with a mean of returns mu and standard deviation of returns
    sigma, on a portfolio of value P

    Parameters
    ----------
    P : TYPE
        DESCRIPTION.
    c : TYPE
        DESCRIPTION.
    mu : TYPE
        DESCRIPTION.
    sigma : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    
    alpha = norm.ppf(1-c, mu, sigma)
    return P - P*(alpha+1)



if __name__ == '__main__':
    
    # Download the Citi Group OHLCV data from 1/1/2010 to 1/1/2014
    start_date = dt.datetime(2010, 1, 1)
    end_date = dt.datetime(2014, 1, 1)
    citi = get_daily_historic_data('C', start_date, end_date)
    
    # Calculate the percentage change
    citi["rets"] = citi["Adj Close"].pct_change()
    
    P = 1e6   # 1,000,000 USD
    c = 0.99  # 99% confidence interval
    mu = np.mean(citi["rets"])
    sigma = np.std(citi["rets"])
    
    var = var_cov_var(P, c, mu, sigma)
    print("Value-at-Risk: $%0.2f" % var)