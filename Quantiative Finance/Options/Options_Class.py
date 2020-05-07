#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 11:42:27 2020

@author: josephgross
"""

import pandas as pd


# Input should actually be a stock object
# From stock object, get the ticker
# Use an API to collec the actual options data
class Options():
    def __init__(self, ticker, current_price, strike_prices, call_prices, put_prices):
        self.ticker = ticker
        self.current_price = current_price
        self.strike_prices = strike_prices
        self.call_prices = call_prices
        self.put_prices = put_prices
        self.options_df = pd.DataFrame()
        
        
    def make_options_df(self):
        self.options_df["Strike Price"] = self.strike_prices
        self.options_df["Call Price"] = self.call_prices
        self.options_df["Put Price"] = self.put_prices
        self.options_df["Ticker"] = self.ticker
        self.options_df["Current Price"] = self.current_price
        self.options_df_get_percent_change_profit()
    
    # Make two columns in the options_df with the stock price necessary to make a profit
    def options_df_get_breakeven_price(self):
        
        # Stock price necessary to make a profit
        self.options_df["Call Breakeven"] = (self.options_df["Strike Price"] + 
                                               self.options_df["Call Price"])
        self.options_df["Put Breakeven"] = (self.options_df["Strike Price"] - 
                                               self.options_df["Put Price"])
    
    # Make two columns in the options_df with the price change necessary to make a profit
    def options_df_get_price_change_profit(self):
        self.options_df_get_breakeven_price()
        
        # Price change in stock price necessary to make a profit
        self.options_df["Call Price Change"] = abs(self.options_df["Call Breakeven"]-
                                                         self.options_df["Current Price"])
        self.options_df["Put Price Change"] = -abs(self.options_df["Put Breakeven"]-
                                                         self.options_df["Current Price"])
        
    # Make two columns in the options_df with the percent change necessary to make a profit
    def options_df_get_percent_change_profit(self):
        self.options_df_get_price_change_profit()
        
        # Percent change in stock price necessary to make a profit
        self.options_df["Call Percent Change"] = round(self.options_df["Call Price Change"]/
                                                        self.options_df["Current Price"]*100,2)
        self.options_df["Put Percent Change"] = round(self.options_df["Put Price Change"]/
                                                        self.options_df["Current Price"]*100,2)
        
    
        
        

        
if __name__ == "__main__":
    strike_prices_SQ = [50,51,52,53,54,55,56]
    call_prices_SQ =[6, 4.95, 3.95, 3.35, 2.77, 2.29, 1.88]
    put_prices_SQ = [1.84, 2.36, 2.62, 3.20, 3.45, 4.0, 4.85]
    current_price_SQ = 53.34
    
    SQ = Options("SQ", current_price_SQ, strike_prices_SQ, call_prices_SQ, put_prices_SQ)
    SQ.make_options_df()
    SQ_df = SQ.options_df
    
        
        