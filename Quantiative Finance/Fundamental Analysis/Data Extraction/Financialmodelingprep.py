#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 16:57:58 2020

@author: josephgross
"""

# ============================================================================
# getting fundamental data from financialmodelingprep.com
# Author - Mayank Rasu

# Please report bugs/issues in the Q&A section
# =============================================================================

import requests
import pandas as pd

link = "https://financialmodelingprep.com/api/v3"
tickers = ["AXP"]


#list of tickers whose financial data needs to be extracted
financial_dir = {}

for ticker in tickers:
    try:
    #getting balance sheet data
        temp_dir = {}
        url = link+"/financials/balance-sheet-statement/"+ticker
        page = requests.get(url)
        fin_dir = page.json()
        for key,value in fin_dir["financials"][0].items():
            temp_dir[key] = value
    #getting income statement data
        url = link+"/financials/income-statement/"+ticker
        page = requests.get(url)
        fin_dir = page.json()
        for key,value in fin_dir["financials"][0].items():
            if key not in temp_dir.keys():
                temp_dir[key] = value
    #getting cashflow statement data
        url = link+"/financials/cash-flow-statement/"+ticker
        page = requests.get(url)
        fin_dir = page.json()
        for key,value in fin_dir["financials"][0].items():
            if key not in temp_dir.keys():
                temp_dir[key] = value
    #getting EV data
        url = link+"/enterprise-value/"+ticker
        page = requests.get(url)
        fin_dir = page.json()
        for key,value in fin_dir["enterpriseValues"][0].items():
            if key not in temp_dir.keys():
                temp_dir[key] = value
    #getting key statistic data
        url = link+"/company-key-metrics/"+ticker
        page = requests.get(url)
        fin_dir = page.json()
        for key,value in fin_dir["metrics"][0].items():
            if key not in temp_dir.keys():
                temp_dir[key] = value
        
    #combining all extracted information with the corresponding ticker
        financial_dir[ticker] = temp_dir
        
    except:
        print("Problem scraping data for ",ticker)
        
#storing information in pandas dataframe
combined_financials = pd.DataFrame(financial_dir)
  