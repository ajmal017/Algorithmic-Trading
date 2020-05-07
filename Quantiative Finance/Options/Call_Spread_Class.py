 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 22:03:45 2020

@author: josephgross
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

        
class Call_Spread():
    def __init__(self, call_1, call_2):
        """
        Initializes a Call_Spread Instance

        Parameters
        ----------
        call_1 : 'Call'
            A Call Object
        call_2 : "Call"
            A Call Object

        Returns
        -------
        None.

        """
        
        # sets the two call objects self.call_1 and self.call_2 in order of expiration date
        self.call_1 = call_1
        self.call_2 = call_2
        
        self.call_1_info_df = self.call_1.call_info_df.copy()
        self.call_2_info_df = self.call_2.call_info_df.copy()
        
        self.ticker = call_1.ticker
        self.original_price = self.call_1.original_price
        
        
        self.call_spread_info_df = pd.DataFrame()
        self.build_call_spread_info_df()
        
      
    def get_general_spread_info_series(self, i, j):
        """
        Creates a pd.Series object with general information about the call spread

        Parameters
        ----------
        i : 'int'
            The index for the desired row from call 1
        j : 'int'
            The index for the desired row from call 1

        Returns
        -------
        'pd,Series'
            Series object with general information about the call spread

        """
        row1 = self.call_1_info_df.iloc[i]
        row2 = self.call_2_info_df.iloc[j]
        general_spread_info_dict = {}
        
        general_spread_info_dict["Ticker"] = row2["Ticker"]
        general_spread_info_dict["Start Date"] = row2["Start Date"]
        general_spread_info_dict["Original Price"] = row2["Original Price"]
        general_spread_info_dict["Capital Commited"] = row1["Capital Committed"] + row2["Capital Committed"]
        
        return pd.Series(general_spread_info_dict)
                
                                 
    def get_call_1_info_series(self, i):  
        """
        Creates a pd.Series with infomation about call 1

        Parameters
        ----------
        i : 'int'
            The index for the desired row from call 1

        Returns
        -------
        'pd,Series'
            Series object with information about call 1 (expires sooner)

        """
        
        row1 = self.call_1_info_df.iloc[i]
        call_1_info_dict = {}
    
        column_names_to_keep = ["Expiration Date", "Time Interval (days)", "Intrinsic Value", 
                                "Time Value", "Premium", "Strike Price", "Type"]
        for column_name in column_names_to_keep:
            call_1_info_dict[column_name] = row1[column_name]
            
        return pd.Series(call_1_info_dict)
        
        
    def get_call_2_info_series(self, j):
        """
        Creates a pd.Series with infomation about call 2

        Parameters
        ----------
        j : 'int'
            The index for the desired row from call 2

        Returns
        -------
        'pd,Series'
            Series object with information about call 2 (expires later)

        """
        
        row2 = self.call_2_info_df.iloc[j]
        call_2_info_dict = {}
    
        column_names_to_keep = ["Expiration Date", "Time Interval (days)", "Intrinsic Value", 
                                "Time Value", "Premium", "Strike Price", "Type"]
        for column_name in column_names_to_keep:
            call_2_info_dict[column_name] = row2[column_name]
            
        return pd.Series(call_2_info_dict)
        
    
    def get_n_percent_change_call_spread_risk_series(self, i, j, n_percent):
        """
        Creates a pd.Series object with information about the risk and reward of the call spread if the underlying asset
        price were to change n_percent

        Parameters
        ----------
        i : 'int'
            The index for the desired row from call 1
        j : 'int'
            The index for the desired row from call 2
        n_percent : 'float'
            Percent that the underlying asset price has changed.

        Returns
        -------
        'pd,Series'
            Series object with risk information about the spread if the underlying asset price were to change
            n_percent

        """
        
        new_price = self.call_2_info_df["Original Price"].iloc[j]*(1+n_percent/100)
        
        return_info = self.get_return_info_series(i, j, new_price)
        return_info["New Price"] = new_price
        columns_to_keep = ["New Price", "Total Call 1 Return", "Total Call 2 Return", "Net Return", "ROI"]
        
        return return_info[columns_to_keep]
        
    
    def build_call_spread_info_df(self):
        """
        Builds a pd.Dataframe with information about the spread. This method combines the series from the previous four
        methods into a multi-index data frame. The dataframe is then assigned to self.call_spread_info. The rows of the
        dataframe created provide information on every possible spread (2 calls, 1 from call 1, 1 rom call 2)

        Returns
        -------
        None.

        """
         
        call_spread_info_list = []
        
        for i in range(self.call_1_info_df.shape[0]):
            for j in range(self.call_2_info_df.shape[0]):
                # combine all series into one multi index series
                info_dict = {"General Info":self.get_general_spread_info_series(i, j), 
                           "Call 1":self.get_call_1_info_series(i), 
                           "Call 2":self.get_call_2_info_series(j),
                           "0% Asset Price Change":self.get_n_percent_change_call_spread_risk_series(i, j, 0),
                           "10% Asset Price Increase":self.get_n_percent_change_call_spread_risk_series(i, j, 10),
                           "-10% Asset Price Decrease":self.get_n_percent_change_call_spread_risk_series(i, j, -10)}
            
                call_spread_info_list.append(pd.concat(info_dict.values(), axis=0, keys=info_dict.keys()))
            
            
        self.call_spread_info_df = pd.concat(call_spread_info_list, axis=1)
        
        
    def get_return_info_series(self, i, j, new_price):
        """
        Creates a pd.Series object with information about the return of the call spread if the underlying asset
        price were to move to a new price

        Parameters
        ----------
        i : 'int'
            The index for the desired row from call 1
        j : 'int'
            The index for the desired row from call 2
        new_price : 'float'
            The new price of the underlying asset

        Returns
        -------
        'pd,Series'
            Series object with risk information about the spread if the underlying asset price were to move 
            to a new price "new_price"

        """
        
        row1 = self.call_1.get_return_info_df(new_price).reset_index().iloc[i]
        row2 = self.call_2.get_return_info_df(new_price).reset_index().iloc[j]
        
        
        return_info = {}
        
        return_info["Ticker"] = self.ticker
        return_info["Current Price"] = new_price
        return_info["Call 1 Strike Price"] = row1["Strike Price"]
        return_info["Call 2 Strike Price"] = row2["Strike Price"]
        return_info["Call 1 Strike Type"] = row1["Type"]
        return_info["Call 2 Strike Type"] = row2["Type"]
        return_info["Capital Commited"] = row1["Capital Committed"] + row2["Capital Committed"]
        
        
        return_info["Call 1 Return / Call"] = row1["Return/Call"]
        return_info["Call 2 Return / Call"] = row2["Return/Call"]
        return_info["Net Return / Call"] = return_info["Call 1 Return / Call"]+return_info["Call 2 Return / Call"]
        
        return_info["Total Call 1 Return"] = return_info["Call 1 Return / Call"]*100
        return_info["Total Call 2 Return"] = return_info["Call 2 Return / Call"]*100
        return_info["Net Return"] = return_info["Total Call 1 Return"]+return_info["Total Call 2 Return"]
        
        return_info["ROI"] = round(return_info["Net Return"]/return_info["Capital Commited"]*100,2)
        
        return pd.Series(return_info)
    
    def get_call_spread_return_info_df(self, new_price):
        """
        Builds a pd.Dataframe with information about the return of the spread if the price of the underlying
        asset were to move to a new price "new_price". This method combines the series collected from the previous 
        methods into a data frame. 

        Parameters
        ----------
        new_price : 'float'
            The new price of the underlying asset

        Returns
        -------
        'pd.DataFrame'
            returns a dataframe with information on the return of a every  possible spread (2 calls, 1 from call 1, 1 rom call 2)
            if the price of the underlying asset were to move to a new price "new_price"

        """
        
        call_spreads_return_list = []
        
        for i in range(self.call_1_info_df.shape[0]):
            for j in range(self.call_2_info_df.shape[0]):
                 call_spreads_return_list.append(self.get_return_info_series(i, j, new_price))
        
        
        return pd.concat(call_spreads_return_list, axis=1)
    
    def display_return_vs_asset_price_change_graph(self, price_range, index, is_percent=False):
        """
        Display a net return vs assset price graph

        Parameters
        ----------
        is_percent: "Boolean", optional
            A boolean that determines whether the inputted price range is a percentage or number
        range : 'float'
            The range of price or percent change values to be graphed (plus or minus range)
        index : 'float'
            index of the spread instance (row) within the dataframe to access

        Returns
        -------
        None.

        """
        
        x_values = []
        y_values = []
       
            
        original_price = self.original_price
            
        for i in range(-price_range, price_range):
            
            if(is_percent):
                new_price = original_price*(1+i/100)
                x_values.append(i)
            else:
                new_price = original_price + i
                x_values.append(new_price)
                
            y_values.append(self.get_call_spread_return_info_df(new_price).T["Net Return"][index])
            
            
        print(self.get_call_spread_return_info_df(new_price).T["Net Return"][index])
        
        
        if(is_percent):
            strike_price_1 = round((self.get_call_spread_return_info_df(new_price).T["Call 1 Strike Price"][index]-original_price)/original_price*100,2)
            strike_price_2 = round((self.get_call_spread_return_info_df(new_price).T["Call 2 Strike Price"][index]-original_price)/original_price*100,2)
            original_price = 0
            title = "Return ($) vs " + self.ticker + " Price Change (%)"
            xlabel = "Price Change (%)"
            ylabel = "Return ($)"
            label1 = "Strike Price - {} ({}%)".format(self.get_call_spread_return_info_df(new_price).T["Call 1 Strike Type"][index], strike_price_1)
            label2 = "Strike Price - {} ({}%)".format(self.get_call_spread_return_info_df(new_price).T["Call 2 Strike Type"][index], strike_price_2)
        else:   
            strike_price_1 = self.get_call_spread_return_info_df(new_price).T["Call 1 Strike Price"][index]
            strike_price_2 = self.get_call_spread_return_info_df(new_price).T["Call 2 Strike Price"][index]
            title = "Return ($) vs " + self.ticker + " Price ($)"
            xlabel = "Price ($)"
            ylabel = "Return ($)"
            label1 = "Strike Price - {} (${})".format(self.get_call_spread_return_info_df(new_price).T["Call 1 Strike Type"][index], strike_price_1)
            label2 = "Strike Price - {} (${})".format(self.get_call_spread_return_info_df(new_price).T["Call 2 Strike Type"][index], strike_price_2)
            
        
        plt.figure()
        plt.title(title)
        
        
        plt.plot(x_values, y_values) 
        plt.axvline(x=strike_price_1, color='k', linestyle='-', 
                    label=label1)
        plt.axvline(x=strike_price_2, color='k', linestyle='--',
                    label=label2)
        plt.axvline(x=original_price, color='b', linestyle='--', label="Original Price (${})".format(self.original_price))
        plt.hlines(y=0, xmin=x_values[0], xmax=x_values[-1])
        
        #slope, intercept = np.polyfit(x_values, y_values, 1)
        
        plt.fill_between(x_values, y_values, where=np.array(y_values)>0, color='g')
        plt.fill_between(x_values, y_values, where=np.array(y_values)<0, color='r')
        
        plt.legend()
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation='45') # rotating tick marks
        plt.show()
        
    
   
        
#======================================================================================  
        
    
   
   
   
   
   
   
   
