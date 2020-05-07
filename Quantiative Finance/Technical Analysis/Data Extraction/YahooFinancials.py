#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 13:20:41 2020

@author: josephgross
"""


from yahoofinancials import YahooFinancials
import pandas as pd
import pandas_datareader as pdr
import datetime as dt

tickers = ["AMZN", "AAPL", "IBM", "FB", ]

close_prices = pd.DataFrame()
start_date = (dt.date.today()-dt.timedelta(3650)).strftime('%Y-%m-%d')
end_date = dt.date.today().strftime('%Y-%m-%d')


attempt=0
drop = []
price_data={}

while (len(tickers) != 0 and attempt < 3): 
    tickers = [j for j in tickers if j not in drop]
    for i in range(len(tickers)):
        try:
           ticker = tickers[i]
           yahoofinancials = YahooFinancials(ticker) 
           json_obj = yahoofinancials.get_historical_price_data(start_date, end_date, 'daily')
           ohlv = json_obj[ticker]['prices']
          
           temp = pd.DataFrame(ohlv)[["formatted_date","open","adjclose", "high", "high", "volume"]]
           temp.set_index("formatted_date",inplace=True)
           temp = temp[~temp.index.duplicated(keep='first')]
           
           close_prices[ticker] = temp["adjclose"]
           
           drop.append(ticker)
        except:
            print("Attempt", attempt, tickers[i], "failed to collect data")
            continue
    attempt += 1
