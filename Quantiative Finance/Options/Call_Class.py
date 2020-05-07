"""
Created on Tue Mar 31 22:03:45 2020

@author: josephgross
"""


import pandas as pd
import numpy as np
        

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
    
    
    
    
