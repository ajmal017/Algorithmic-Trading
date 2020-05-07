#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 14:48:50 2020

@author: josephgross
"""

API_KEY = 'ZZ4PFN9ATU1ASPAN'
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
import matplotlib.plot as plt
import pandas as pd


class TechnicalIndicators:
    def __init__(self, ticker):
        self.api_key='ZZ4PFN9ATU1ASPAN'
        self.stock_name=ticker
        self.macd_data=self.macd()
        self.rsi_data=self.rsi()
        self.bbands_data=self.bbands()
        self.close_data=self.close()
        self.sma_data=self.sma()
    def macd(self):
        a = TechIndicators(key=self.api_key, output_format='pandas')
        data, meta_data=a.get_macd(symbol=self.stock_name,interval='daily')
        return data
    def rsi(self):
        b=TechIndicators(key=self.api_key,output_format='pandas')
        data,meta_data = b.get_rsi(symbol=self.stock_name,interval='daily',time_period=14)
        return data
    def bbands (self):
        c=TechIndicators(key=self.api_key,output_format='pandas')
        data,meta_data=c.get_bbands(symbol=self.stock_name)
        return data
    def sma(self):
        d= TechIndicators(key=self.api_key, output_format='pandas')
        data, meta_data = d.get_sma(symbol=self.stock_name,time_period=30)
        return data
    def close(self):
        d=TimeSeries(key=self.api_key,output_format='pandas')
        data,meta_data=d.get_daily(symbol=self.stock_name,outputsize='full')
        return data
        
if __name__ == "__main__":
    TI=TechnicalIndicators("AAPL")
    rsi_data = TI.rsi()
    plt.plot(rsi_data)
    plt.show()

ts = TimeSeries(key=API_KEY, output_format='pandas')
data,meta_data = ts.get_intraday(symbol="MSFT", interval='1min', outputsize='full')
data.columns = ["open", "high", "low", "close", "volume"]
