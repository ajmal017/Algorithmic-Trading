#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 21:40:04 2020

@author: josephgross
"""

import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import pandas_datareader as pdr
import requests

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
        self.get_daily_returns()
        
    def get_financial_data(self):
        try:
           link = "https://financialmodelingprep.com/api/v3"
            
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
        
        
    def get_daily_returns(self):
        self.historical_price_data["Daily Return"] = self.historical_price_data["Adj Close"].pct_change()
        

#======================================================================================     


class Technical_Indicators():
    def __init__(self, stock):
        self.stock = stock
        
        self.MACD = pd.DataFrame()
        self.get_MACD_df(12,26, 9)
        
        self.ATR = pd.DataFrame()
        self.get_ATR_df(14)
        
        self.BollBnd = pd.DataFrame()
        self.get_BollBnd_df(2, 20)
        
        
    def get_MACD_df(self, fast, slow, signal):
        MACD = self.stock.historical_price_data[["Daily Return","Adj Close"]].copy()
        MACD["MA_Fast"] = MACD["Daily Return"].ewm(span=fast, min_periods=fast).mean()
        MACD["MA_Slow"] = MACD["Daily Return"].ewm(span=slow, min_periods=slow).mean()
        MACD["MACD"] = MACD["MA_Fast"]-MACD["MA_Slow"]
        MACD["Signal Line"] = MACD["MACD"].ewm(span=signal, min_periods=signal).mean()
        MACD.dropna(inplace=True)
        self.MACD = MACD
        
    def display_MACD(self, time_delta):
        #self.MACD[["Adj Close", "MACD", 'Signal Line']].plot(subplots=True, sharex=True, 
         #                                                    title="MACD Indicator", grid=False,
         #                                                    color=['blue','black', 'red'])
        
        df= self.MACD.tail(time_delta)
        plt.figure()
        plt.title("MACD")
        
        # Adj Close
        ax1=plt.subplot(211)
        plt.plot(df.index, df["Adj Close"], 'blue') # plot price data
        ax1.legend(["Adj Close Price"], loc="best") # adding a legend
        plt.setp(ax1.get_xticklabels(), visible=False) # hiding axis ticks
        ax1.set_title(self.stock.ticker + " MACD Last " + str(time_delta) + " Days") # setting a title
        
        # MACD and signal line
        ax2=plt.subplot(212, sharex=ax1)
        plt.plot(df.index, df["MACD"],'black', df.index, df['Signal Line'], 'red') # plotting data
        ax2.legend(["MACD", "Signal Line"], loc="best")  # adding a legend
        
        plt.xticks(rotation='45') # rotating tick marks
        plt.show()
        
    def get_ATR_df(self, n):
        df = self.stock.historical_price_data[["High","Low","Adj Close"]].copy()
        df["H-L"] = abs(df["High"]-df["Low"])
        df["H-PC"] = abs(df["High"]-df["Adj Close"].shift(1))
        df["L-PC"] = abs(df["Low"]-df["Adj Close"].shift(1))
        df["TR"]= df[["H-L","H-PC","L-PC"]].max(axis=1, skipna=False)
        df["ATR"] = df["TR"].rolling(n).mean()
        self.ATR = df[["ATR", "TR"]]
        
    def get_BollBnd_df(self, n, m):
    
        df = self.stock.historical_price_data[["High","Low","Adj Close"]].copy()
        df["MA"] = df['Adj Close'].rolling(n).mean()
        df["BB_up"] = df["MA"] + n*df['Adj Close'].rolling(m).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
        df["BB_dn"] = df["MA"] - n*df['Adj Close'].rolling(m).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
        df["BB_width"] = df["BB_up"] - df["BB_dn"]
        df.dropna(inplace=True)
        self.BollBnd = df
        
    def display_ATR_BollBnd(self, time_delta):
    
        df1 = self.BollBnd.tail(time_delta)
        df2 = self.ATR.tail(time_delta)
        plt.figure()
        plt.title("ATR and Bollinger Bands")
        
        # Bollinger Bands
        ax1=plt.subplot(211)
        plt.plot(df1.index, df1["Adj Close"], 'blue', df1.index, df1["BB_up"], 'black', df1.index, df1["BB_dn"], 'black') # plot price data
        ax1.legend(["Adj Close Price", "Bollinger Bands"], loc="best") # adding a legend
        plt.setp(ax1.get_xticklabels(), visible=False) # hiding axis ticks
        ax1.set_title(self.stock.ticker + " Bollinger Bands " + str(time_delta) + " Days") # setting a title
        ax1.fill_between(df1.index, df1["BB_up"], df1["BB_dn"], 1)
        
        # MACD and signal line
        ax2=plt.subplot(212, sharex=ax1)
        plt.plot(df2.index, df2["ATR"],'red') # plotting data
        ax2.legend(["ATR"], loc="best")  # adding a legend
        
        plt.xticks(rotation='45') # rotating tick marks
        plt.show()
           
        
        
        
if __name__ == "__main__":
   ticker="AAPL"
   start_date = dt.date.today() - dt.timedelta(365)
   end_date = dt.date.today()
   
   apple_stock = Stock(ticker, start_date, end_date)
   
   apple_TI = Technical_Indicators(apple_stock)
   apple_TI.display_MACD(50)
   apple_TI.display_ATR_BollBnd(50)