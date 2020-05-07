#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 11 18:26:46 2020

@author: josephgross
"""


import datetime as dt
import pprint
import pandas as pd

import statsmodels.tsa.stattools as ts

from alpha_vantage.timeseries import TimeSeries


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


if __name__ == "__main__":
    
    # Download the the Amazon OLCV data from 1/1/2000 to 1/1/2015
    start_date = dt.datetime(2000, 1, 1)
    end_date = dt.datetime(2015, 1, 1)
    amzn = get_daily_historic_data_alphavantage('AMZN', start_date, end_date)
    
    # Output the results of the Augmented Dickey-Fulller test for Amazon
    # with a lag order value of 1
    pprint.pprint(ts.adfuller(amzn["Adj Close"].tolist(), 1))