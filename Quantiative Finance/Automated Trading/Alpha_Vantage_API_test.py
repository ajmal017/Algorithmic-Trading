#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 11:05:15 2020

@author: josephgross
"""


from alpha_vantage.timeseries import TimeSeries
import matplotlib.pyplot as plt
import datetime as dt

ALPHA_VANTAGE_API_KEY = 'YZZ4PFN9ATU1ASPAN'



ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='json')
data, meta_data = ts.get_daily_adjusted(symbol='MSFT', outputsize='full')



prices = []
for date_str in sorted(data.keys()):
    bar = data[date_str]
    prices.append(
        (
            date_str,
            float(bar['1. open']),
            float(bar['2. high']),
            float(bar['3. low']),
            float(bar['4. close']),
            int(bar['6. volume']),
            float(bar['5. adjusted close'])
            )
        )
    