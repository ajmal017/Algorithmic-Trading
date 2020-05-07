 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 22:03:45 2020

@author: josephgross
"""


import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt

# Add a filter method that returns a call_info_df (takes in parameters: type="ATM"/"OOTM"/"ITM", Expiration Date) 
# Create a new constructor with input parameters: ticker, original_price,  start_date, call_info_df, is_long
class Call():
        
    def __init__(self, ticker, original_price,  start_date, external_call_info_dict, is_long):
        """
        Initialize the Call instance

        Parameters
        ----------
        ticker : 'str'
            Ticker describing the asset that the call represents
        original_price : 'float'
            Asset Price at the time the call is purchased
        start_date : 'datetime'
            The date the contract is opened. Will typically be today
        external_call_info_dict : 'dict'
            Dictionary containing call information. Keys are the expiration date, and the values are another dictionary.
            The nested dictionary has keys = ["Strike Prices", "Premiums"] and values of type pd.Series
        is_long : 'Boolean'
            A boolean describing whether the call is long or short. This is used to calculate return information

        Returns
        -------
        None.

        """
        
        self.ticker = ticker
        self.original_price = original_price
        self.start_date = start_date
        self.is_long = is_long
        
        self.call_info_df = pd.DataFrame()
        self.build_call_info_df(external_call_info_dict)
        
        
        
    def get_type(self):
        """
        Creates a series with the option strike type (ITM, ATM, OR OOTM)
        Threshhold for ATM is a strike price within one percent of the original price

        Returns
        -------
        pd.Series
        """
        
        if(self.is_long):
            action_type = "Long"
        else:
            action_type = "Short"
        
        df = self.call_info_df.copy()
        delta_price = abs(df["Original Price"] - df["Strike Price"])
        
        df["Type"] = np.where(delta_price/df["Original Price"]*100 < 1,
                              action_type + " ATM",
                              np.where(df["Original Price"] < df["Strike Price"], #if the strike price is not ATM then check for ITM of OOTM
                                       action_type + " OOTM",
                                       action_type + " ITM")
                              )
        return df["Type"]
    
    def create_breakeven_information(self):
        """
        Creates columns with information about when the call breaks even

        Returns
        -------
        None.

        """
        
        # Asset price necessary to break even (neither long nor short makes money)
        self.call_info_df["Breakeven Price"] = self.call_info_df["Strike Price"] + self.call_info_df["Premium"]
        
        # Asset price/percent change necessary to break even (neither long nor short makes money)
        self.call_info_df["Breakeven Price Change"] = self.call_info_df["Breakeven Price"] - self.call_info_df["Original Price"]
        self.call_info_df["Breakeven Percent Change"] = round(self.call_info_df["Breakeven Price Change"] /
                                                            self.call_info_df["Original Price"]*100, 2)
    
    def get_temp_df(self, external_call_info_dict):
        """
        Takes apart the nested dictionary and converts it into a dataframe with information

        Parameters
        ----------
        external_call_info_dict : 'dict'
            Dictionary containing call information. Keys are the expiration date, and the values are another dictionary.
            The nested dictionary has keys = ["Strike Prices", "Premiums"] and values of type pd.Series

        Returns
        -------
        df : pd.DataFrame
            Dataframe with information on the call. (Expiration date, strike prices, and premiums)

        """
        
        temp_list = []
        for key in external_call_info_dict.keys():
            temp_dict = external_call_info_dict[key]
            temp_list.append(pd.concat(temp_dict.values(), axis=1, keys=temp_dict.keys()))
        
        df = (pd.concat(temp_list, keys=external_call_info_dict.keys()).reset_index()
              .rename(columns={"level_0":"Expiration Date"}).drop("level_1", axis=1))
        
        return df
    
    def build_call_info_df(self, external_call_info_dict):
        """
        Constructs the call_info_df which contains all the call information

        Returns
        -------
        None.

        """
        
        # Takes apart the nested dictionary and converts it into a dataframe with information
        df = self.get_temp_df(external_call_info_dict)
        
        self.call_info_df["Strike Price"] = df["Strike Prices"]
        self.call_info_df["Original Price"] = self.original_price
        self.call_info_df["Start Date"] = self.start_date
        self.call_info_df["Expiration Date"] = df["Expiration Date"]
        self.call_info_df["Ticker"] = self.ticker
        self.call_info_df["Type"] =  self.get_type()
        
        self.call_info_df["Premium"] = df["Premiums"]
        self.call_info_df["Intrinsic Value"] = np.where(self.call_info_df["Original Price"] > self.call_info_df["Strike Price"],
                                                      self.call_info_df["Original Price"] - self.call_info_df["Strike Price"],
                                                      0)
        self.call_info_df["Time Value"] = self.call_info_df["Premium"] - self.call_info_df["Intrinsic Value"]
        self.call_info_df["Time Interval (days)"] = self.call_info_df.apply(lambda row: (row["Expiration Date"] - row["Start Date"]).days, axis=1)
        
        if(self.is_long):
            self.call_info_df["Capital Committed"] = self.call_info_df["Premium"] * 100
        else:
            self.call_info_df["Capital Committed"] = 0
        
        self.create_breakeven_information()
        
      

    def get_return_info_df(self, current_price):
        """
        Returns a dataframe with information about returns based on a new price and whether the call is long or short
        Calculates the value of a call at a certain price point

        Parameters
        ----------
        current_price : 'float'
            The current price of the asset the call represents

        Returns
        -------
        pd.DataFrame()
            Pandas Dataframe with infomation on the return the call generates

        """
        
        return_info = self.call_info_df.copy().drop(["Breakeven Price Change", "Breakeven Percent Change"], axis=1)
        return_info["Current Price"] = current_price
        
        
        
        if(self.is_long):
            IV =  (current_price-self.call_info_df["Strike Price"]-self.call_info_df["Premium"])
            return_info["Return/Call"] = np.where(self.call_info_df["Strike Price"] <= current_price,
                                             IV, -self.call_info_df["Premium"])
        else:
            return_info.drop(["Breakeven Price"], axis=1, inplace=True)
            return_info["Return/Call"] = np.where(self.call_info_df["Strike Price"] >= current_price, # option expires worthless
                                             self.call_info_df["Premium"], # net the premium when short
                                             (self.call_info_df["Premium"]-
                                              (current_price-self.call_info_df["Strike Price"]))) # lose the intrinsic value
        
        return_info["Total Return"] = return_info["Return/Call"]*100
        
        
        return return_info.set_index("Ticker")

#=================================================================================

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

if __name__ == "__main__":
   ticker="BA"
   original_price = 267.99
   start_date = dt.date.today()
   
   
   
   short_strike_prices_1 = [260, 262.5, 265, 267.5, 270, 272.5, 275, 277.5]
   short_premiums_1 = [11.45, 9.7, 7.9, 6.45, 4.95, 3.75, 2.77, 2.05]
   short_expiration_date_1 = dt.date(2020, 4, 17) # YY-mm-dd
   
   short_strike_prices_2 = [260, 262.5, 265, 267.5, 270, 272.5, 275, 277.5]
   short_premiums_2 = [14.2, 12.45, 10.5, 9.25, 7.8, 6.85, 5.5, 4.5]
   short_expiration_date_2 = dt.date(2020, 4, 24) # YY-mm-dd
   
   short_strike_prices_3 = [260, 262.5, 265, 267.5, 270, 272.5, 275, 277.5]
   short_premiums_3 = [17, 15.15, 14, 12.55, 11.15, 9.85, 8.6, 7.3]
   short_expiration_date_3 = dt.date(2020, 5, 1) # YY-mm-dd
   
   external_short_call_info = {}
   #external_short_call_info[short_expiration_date_1] = {"Premiums":pd.Series(short_premiums_1), "Strike Prices":pd.Series(short_strike_prices_1)}
   #external_short_call_info[short_expiration_date_2] = {"Premiums":pd.Series(short_premiums_2), "Strike Prices":pd.Series(short_strike_prices_2)}
   #external_short_call_info[short_expiration_date_3] = {"Premiums":pd.Series(short_premiums_3), "Strike Prices":pd.Series(short_strike_prices_3)}

   
   
   long_strike_prices = [250, 255, 260, 265, 270, 280, 290, 300]
   long_premiums = [53.95, 51.75, 48.75, 46, 43.85, 38.7, 34.5, 31]
   long_expiration_date = dt.date(2022, 1, 21)  # YY-mm-dd
   
   external_long_call_info = {}
   #external_long_call_info[long_expiration_date] = {"Premiums":pd.Series(long_premiums), "Strike Prices":pd.Series(long_strike_prices)}
   
   
   
   
   
   
   
   short_strike_prices_test = [280]
   short_premiums_test = [10]
   short_expiration_date_test = dt.date(2020, 5, 1) # YY-mm-dd
   external_short_call_info[short_expiration_date_test] = {"Premiums":pd.Series(short_premiums_test), "Strike Prices":pd.Series(short_strike_prices_test)}
   
   
   long_strike_prices_test = [250, 240, 230]
   long_premiums_test = [17, 30, 45]
   long_expiration_date_test = dt.date(2022, 1, 21)  # YY-mm-dd
   external_long_call_info[long_expiration_date_test] = {"Premiums":pd.Series(long_premiums_test), "Strike Prices":pd.Series(long_strike_prices_test)}
   
   
   
   
   short_call = Call(ticker, original_price,  start_date, external_short_call_info, is_long=False)
   short_call_info = short_call.call_info_df
   
   # add a quantity to the call construction
   long_call = Call(ticker, original_price,  start_date, external_long_call_info, is_long=True)
   long_call_info = long_call.call_info_df
   
   
   BA_PMCC = Call_Spread(short_call, long_call)
   
   df_call_spread_info = BA_PMCC.call_spread_info_df
   
   new_price = 300
   df_return_info = BA_PMCC.get_call_spread_return_info_df(new_price)
   
   
   
   for i in range(df_return_info.T.shape[0]):
       BA_PMCC.display_return_vs_asset_price_change_graph(30, i, is_percent=False)
   

   
   
   
   
