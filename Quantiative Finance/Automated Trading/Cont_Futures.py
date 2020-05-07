#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 21:11:42 2020

@author: josephgross
"""


import datetime

import numpy as np
import pandas as pd
import quandl


# Replace with your Quandl API Key
AUTH_TOKEN = "ThxvLe6m5vSEczXUYEWp"

def futures_rollover_weights(start_date, expiry_dates, contracts, rollover_days=5):
    """
    This constructs a pandas DataFrame that contains weights (between 0.0 and 1.0)
    of contract positions to hold in order to carry out a rollover of rollover_days 
    prior to the expiration of the earliest contract. The matrix can then be 'multiplied'
    with another DataFrame containing the settle prices of each contract in order to produce 
    a continuous time series futures contract.

    Parameters
    ----------
    start_date : datetime
        The date the first contract is opened.
    expiry_dates : TYPE
        The latest expiration date of the last contract.
    contracts : list
        A list of futures contracts
    rollover_days : int, optional
        The number of rollover days to take into account in the calculation. The default is 5.

    Returns
    -------
    'pd.DataFrame'
        A pandas dataframe that contains the product of the rellover weights matrix and the 
        dataframe with the futures contracts information

    """
    
    # Construct a sequence of dates beginning from the earliest contract start
    # date to the end date of the final contract
    dates = pd.date_range(start_date, expiry_dates[-1], freq='B')


    # Create the 'roll weights' DataFrame that will store the multipliers for 
    # each contract (between 0.0 and 1.0)
    roll_weights = pd.DataFrame(np.zeros((len(dates), len(contracts))),
                                index=dates, columns=contracts)
    prev_date = roll_weights.index[0]
    
    
    # Loop through each contract and creaate the specific weightings for 
    # each contact depending upon the settlement date and rollover_days
    for i, (item, ex_date) in enumerate(expiry_dates.iteritems()):
        if i < len(expiry_dates) - 1:
            roll_weights.loc[prev_date:ex_date - pd.offsets.BDay(), item] = 1
            roll_rng = pd.date_range(end=ex_date - pd.offsets.BDay(),
                                     periods=rollover_days + 1, freq='B')
            
            
            # Create a sequence of roll weights (i.e. [0.0, 0.2, ..., 0.8, 1.0])
            # and use these to adjust the weightings of each future
            decay_weights = np.linspace(0, 1, rollover_days+1)
            roll_weights.loc[roll_rng, item] = 1 - decay_weights
            roll_weights.loc[roll_rng, expiry_dates.index[i+1]] = decay_weights
        else:
            roll_weights.loc[prev_date:, item] = 1
        
        prev_date = ex_date
    
    return roll_weights
    
    
 # ===========================================================================   
    
    
if __name__ == "__main__":
    # Download the current Front and Back (near and far) futures contracts
    # for WTI Crude, traded on NYMEX, from Quandl.com. You will need to adjust
    # the contracts to reflect your current near/far contracts 
    # depending upon the point at which you read this
    cme_near = quandl.get("CHRIS/CME_CL1", authtoken=AUTH_TOKEN)
    cme_far = quandl.get("CHRIS/CME_CL2", authtoken=AUTH_TOKEN)
    cme = pd.DataFrame({'CL1': cme_near['Settle'],
                        'CL2': cme_far['Settle']}, index=cme_far.index)
    
    # Create the dictionary of expiry dates for each contract
    expiry_dates = pd.Series({'CL1': datetime.datetime(2020, 3, 21),
                              'CL2': datetime.datetime(2020, 4, 11)}).sort_values()
    
    
    # Obtain the rollover weighting matrix/DataFrame
    weights = futures_rollover_weights(cme_near.index[0], expiry_dates, cme.columns)
    
    
    # Construct the continuous future of the WTI CL contracts
    cme_cts = (cme * weights).sum(axis=1).dropna()
               
    # Output the merged series of contract settle prices
    print(cme_cts.tail(60))