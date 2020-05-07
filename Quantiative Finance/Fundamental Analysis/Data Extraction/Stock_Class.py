#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 16:04:31 2020

@author: josephgross
"""


import pandas_datareader as pdr
import datetime as dt
import requests
import pandas as pd

link = "https://financialmodelingprep.com/api/v3"

class Stock():
    
    def __init__(self, ticker, start_date, end_date):
        self.ticker = ticker
        self.start_date = start_date.strftime('%Y-%m-%d')
        self.end_date = end_date.strftime('%Y-%m-%d')
        
        self.historical_price_data = pd.DataFrame()
        self.get_historical_price_data()
        
        self.get_financial_data()
        
    def get_historical_price_data(self):
        attempt = 0
        while(attempt<3):
            try:
                temp = pdr.get_data_yahoo(self.ticker,self.start_date, self.end_date)
                temp.dropna(inplace=True)
           
                self.historical_price_data = temp.fillna(method='bfill')
            except:
                print("Attempt", attempt, self.ticker, "failed to collect data")
                continue
            attempt += 1
        
    def get_financial_data(self):
        try:
           
           #getting balance sheet data
           links = [link+"/financials/balance-sheet-statement/"+self.ticker,
                    link+"/financials/income-statement/"+self.ticker,
                    link+"/financials/cash-flow-statement/"+self.ticker,
                    link+"/enterprise-value/"+self.ticker,
                    link+"/company-key-metrics/"+self.ticker]
           
           temp_dir = {}
           for url in links:
               page = requests.get(url)
               fin_dir = page.json()
               if('metrics' in url):
                   for key,value in fin_dir["metrics"][0].items():
                       temp_dir[key] = value
               if('enterprise' in url):
                   for key,value in fin_dir["enterpriseValues"][0].items():
                       temp_dir[key] = value      
               elif('financials' in url):
                   for key,value in fin_dir["financials"][0].items():
                       temp_dir[key] = value   
        
        except:
            print("Problem scraping data for ",self.ticker)
        
        financial_dir = {}
        financial_dir[self.ticker] = temp_dir
        self.financial_data = pd.DataFrame(financial_dir)
            
            
if __name__ == "__main__":
   ticker="AAPL"
   start_date = dt.date.today() - dt.timedelta(365)
   end_date = dt.date.today()
   
   apple_stock = Stock(ticker, start_date, end_date)
            
            
            
            