 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 22:03:45 2020

@author: josephgross
"""


import pandas as pd
import numpy as np


class Short_Call():
    def __init__(self, ticker, original_price, strike_prices, premiums):
        self.ticker = ticker
        self.original_price = original_price
        self.strike_prices = strike_prices
        self.premiums = premiums
        self.options_df = pd.DataFrame()
        self.make_options_df()
        
        self.profit_loss_info = pd.DataFrame()
        
        
    def make_options_df(self):
        self.options_df["Ticker"] = self.ticker
        self.options_df["Strike Price"] = self.strike_prices
        self.options_df["Premium"] = self.premiums
        self.options_df["Original Price"] = self.original_price
        
    def options_df_get_breakeven_information(self):
        # Stock price necessary to make a profit
        self.options_df["Breakeven Price"] = self.options_df["Strike Price"] + self.options_df["Premium"]
        
        self.options_df["Breakeven Price Change"] = self.options_df["Breakeven Price"] - self.options_df["Original Price"]
        self.options_df["Breakeven Percent Change"] = round(self.options_df["Breakeven Price Change"] /
                                                            self.options_df["Original Price"]*100, 2)
       
    # Will become more complete with LEAP call data
        # Add in the price needed at which the call will give a 10% loss
        # Price/Percent change from original to that 
        # Need LEAP data to know how much cash is commited
    def get_ROI_info(self, current_price):
        
        ROI_info = pd.DataFrame()
        
        ROI_info["Original Price"] = self.options_df["Original Price"]
        ROI_info["Current Price"] = current_price
       
        ROI_info["Percent Change"] = round((ROI_info["Current Price"]-self.options_df["Original Price"]) / self.options_df["Original Price"] * 100,2)
        
        # When the price is above the strike price, profit/loss:
        # premium - (current price - strike price) per stock/contract
        ROI_info["Total Profit/Loss"] = np.where(ROI_info["Current Price"] < self.options_df["Strike Price"],
                                             self.options_df["Premium"]*100, 
                                             (self.options_df["Premium"]-
                                              (ROI_info["Current Price"]-self.options_df["Strike Price"]))*100)
        
        return ROI_info
        
        
if __name__ == "__main__":
   ticker="AAPL"
   original_price = 254.29
   strike_prices = [245, 247.5, 250, 252, 255, 257, 260, 262]
   premiums = [17.35, 15.65, 13.95, 12.5, 9.25, 7.6, 6.3, 5.2]
   
   AAPL_short_call = Short_Call(ticker, original_price, strike_prices, premiums)
   
   price_decrease_df = AAPL_short_call.get_ROI_info(0.9*original_price)
   price_increase_df = AAPL_short_call.get_ROI_info(1.1*original_price)
   
