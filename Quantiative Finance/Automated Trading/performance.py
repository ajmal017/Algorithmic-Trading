#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 10:23:38 2020

@author: josephgross
"""


import numpy as np
import pandas as pd


def create_sharpe_ratio(returns, periods=252):
    """
    Create the Sharpe ratio for the strategy, based on a 
    benchmark of zero (i.e. no risk-free information)

    Parameters
    ----------
    returns : 'pd.Series'
        A Pandas Series object representing period percentage returns.
    periods : 'int', optional
        Daily (252., Hourly (252*6.5), Minutley(252*6.5*60) etc. 
        The default is 252.

    Returns
    -------
    'float'
        The Sharpe Ratio.

    """
    
    return np.sqrt(periods) * (np.mean(returns) / np.std(returns))


def create_drawdowns(pnl):
    """
    Calculate the largest peak-to_trough drawdown of the PnL curve
    as well as the duration of the drawdown. Requires that the 
    pnl_returns is a Pandas Series object.

    Parameters
    ----------
    pnl : 'pd.Series'
        A Pandas Series object representing period percentage returns.

    Returns
    -------
    'pd.Series'
        Pandas Series with the drawdown information
    'float'
        Highest peak-to-trough drawdown.
    'float'
        Highest peak-to-trough duration.

    """
    
    # Calculate the cumulative returns curve
    # and set up the High Water Mark
    hwm = [0]
    
    # Create the drawdown and duration series
    idx = pnl.index 
    drawdown = pd.Series(index=idx)
    duration = pd.Series(index=idx) 
    
    # Loop over the index range
    for t in range(1, len(idx)):
        hwm.append(max(hwm[t-1], pnl[t]))
        drawdown[t] = (hwm[t] - pnl[t])
        duration[t] = (0 if drawdown[t] == 0 else duration[t-1]+1)
        
    return drawdown, drawdown.max(), duration.max()