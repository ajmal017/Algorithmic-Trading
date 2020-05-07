#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 12:11:21 2020

@author: josephgross
"""


from datetime import datetime as dt
import pandas as pd
from alpha_vantage.timeseries import TimeSeries

ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co'
ALPHA_VANTAGE_TIME_SERIES_CALL = 'query?function=TIME_SERIES_DAILY_ADJUSTED'
COLUMNS = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']

class AlphaVantage(object):
    """
    Encapsulates calls to the AlphaVantage API with a provided API key.
    """
    
    def __init__(self, api_key='YZZ4PFN9ATU1ASPAN'):
        """
        Inititalize the AlphaVantage instance
        
        Paramaters
        ----------
        api_key = 'str', optional
            The API key for thr associated AlphaVantage account
        """
        
        self.api_key = api_key
        
    

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