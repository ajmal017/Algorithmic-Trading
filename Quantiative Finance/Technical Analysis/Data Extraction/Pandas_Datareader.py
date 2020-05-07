#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 13:20:41 2020

@author: josephgross
"""

import pandas as pd
import pandas_datareader as pdr
import datetime as dt
import matplotlib.pyplot as plt

tickers = ["SQ", "SHOP", "NVCR", "ACAD"]

close_prices = pd.DataFrame()
start_date = (dt.date.today()-dt.timedelta(1500)).strftime('%Y-%m-%d')
end_date = dt.date.today().strftime('%Y-%m-%d')


attempt=0
drop = []

while (len(tickers) != 0 and attempt < 3): 
    tickers = [j for j in tickers if j not in drop]
    for i in range(len(tickers)):
        try:
           ticker = tickers[i]
          
           temp = pdr.get_data_yahoo(ticker,start_date, end_date)
           temp.dropna(inplace=True)
           
           close_prices[ticker] = temp["Adj Close"]
           drop.append(ticker)
        except:
            print("Attempt", attempt, tickers[i], "failed to collect data")
            continue
    attempt += 1
    
close_prices.fillna(method='bfill', inplace = True)


# Mean, Median, Standard Deviation, Daily Return
mean = close_prices.mean(axis=0)
median = close_prices.median(axis=0)
standard_deviation = close_prices.std(axis=0)

daily_return = close_prices.pct_change()
five_day_return = close_prices/close_prices.shift(5)-1
mean_daily_return = daily_return.mean()
standard_deviation_daily_return = daily_return.std()

# Rolling mean and standard deviation
rolling_mean = daily_return.rolling(window=20, min_periods=20).mean() # Simple moving average
rolling_standard_deviation = daily_return.rolling(window=20).mean()

# Exponential moving average (more weight for more recent data)
exponential_moving_average = daily_return.ewm(span=20, min_periods=20).mean() 
exponential_moving_std = daily_return.ewm(span=20, min_periods=20).std() 


# Data visualizations (pandas plot functions)
cp_standardized = (close_prices-close_prices.mean())/close_prices.std()
cp_standardized.plot(subplots=True, sharex=True, sharey=True, layout=(4,1), 
                     title="Stock Evolution", grid=False)

# Pyplot demo
plt.bar(daily_return.columns, daily_return.mean().reset_index.drop("Date", axis=1))

#MACD

