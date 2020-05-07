#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 10:00:09 2020

@author: josephgross
"""


import datetime as dt
from alpha_vantage.timeseries import TimeSeries
import time
import warnings

import mysql.connector
from mysql.connector import Error


ALPHA_VANTAGE_API_KEY = 'YZZ4PFN9ATU1ASPAN'
ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co'
ALPHA_VANTAGE_TIME_SERIES_CALL = 'query?function=TIME_SERIES_DAILY_ADJUSTED'

TICKER_COUNT = 505 # change this to 500 to download all tickers
WAIT_TIME_IN_SECONDS = 10 # adjust how frequently the API is called



# Obtain a database connection to the MySQL instance
db_host = '127.0.0.1'
db_user = 'sec_user'
db_password = 'UZHuYbneFK2'
db_name = 'securities_master'


def obtain_list_of_db_tickers():
    """
    
    Obtains a list of the ticker symbols in the database

    Returns
    -------
    'list' 
        list of tuples containing the symbol id and ticker

    """
    
    con = mysql.connector.connect(
                        user=db_user, 
                        password=db_password,
                        host=db_host,
                        database=db_name)
    
    cursor = con.cursor()
    cursor.execute("SELECT id, ticker FROM symbol")
    #con.commit()
    data = cursor.fetchall()
    
    return [(d[0], d[1]) for d in data]


def get_daily_historic_data_alphavantage(ticker):
    """
    
    Use the generated API call to query AlphaVantage with the 
    appropriate API key and return a list of price tuples for 
    a particular ticker

    Parameters
    ----------
    ticker : 'str'
        The ticker of a stock which will be used to retrieve price data
        from alpha_vantage

    Returns
    -------
    'list'
            List of tuples with historical price data based on a 
            specific ticker

    """
    
    try:
        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='json')
        data, meta_data = ts.get_daily_adjusted(symbol=ticker, outputsize='full')
    except Exception as e:
        print(
            "Could not download AlphaVantage data for %s ticker "
            "(%s)...skipping." % (ticker, e)
        )
        return []
    else:
        prices = []
        start_date = dt.date.today() - dt.timedelta(weeks=25) # Only need 6 months of data
        end_date = dt.date.today()
        delta = (end_date - start_date).days
        
        date_strings = [(start_date + dt.timedelta(i)).strftime('%Y-%m-%d') for i in range(delta)
                        if (start_date + dt.timedelta(i)).strftime('%Y-%m-%d') in data.keys()]
        
        for date_str in date_strings:
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
    
    return prices


def insert_daily_data_into_db(data_vendor_id, symbol_id, daily_data):
    """
    
    Takes a list of tuples of daily data and adds it to the MySQL
    database. Appends the vendor ID and symbol ID to the data

    Parameters
    ----------
    data_vendor_id : 'int'
        Integer to be assigned to a specific vendor.
    symbol_id : 'int'
        The symbol id of the desired ticker/instrument
    daily_data : 'list'
        List of tuples containing daily historical data on the desired instrument

    Returns
    -------
    None.

    """
    
    now = dt.datetime.utcnow()
    
    # Amend the data to include the vendor ID and symbol ID
    daily_data_to_insert = [
        (data_vendor_id, symbol_id, d[0], now, now,
        d[1], d[2], d[3], d[4], d[5], d[6]) 
        for d in daily_data
    ]
    
    # Create the insert strings'
    column_names = (
        'data_vendor_id, symbol_id, price_date, created_date, '
        'last_updated_date, open_price, high_price, low_price, '
        'close_price, volume, adj_close_price'
    )
    query = "INSERT INTO daily_price({}) " \
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s)".format(column_names)
   
    
    #print("---------------------")
    #print(query)
    #print("---------------------")
       
    # Using the MySQL connection, carry out and INSERT INTO for every symbol
    try:
        con = mysql.connector.connect(
                                user=db_user, 
                                password=db_password,
                                host=db_host,
                                database=db_name)
        cursor = con.cursor()
        cursor.executemany(query, daily_data_to_insert)
        
        con.commit()
        
    except Error as error:
        print(error)
        
    finally:
        cursor.close()
        con.close()
        
        
# ===========================================================================
        
        
if __name__ == "__main__":
    
    # This ignore the warnings regarding Data Truncation
    # from the AlphaVantage precision to Decimal(19,4) datatypes
    warnings.filterwarnings('ignore')
    
    
    # Loop over the ticker and insert the daily historical 
    # data into the database
    tickers = obtain_list_of_db_tickers()[:TICKER_COUNT]
    lentickers = len(tickers)
    
    skipped = []
    for i, t in enumerate(tickers):
        print(
            "Adding data for %s: %s out of %s" %
            (t[1], i+1, lentickers)
        )
        av_data = get_daily_historic_data_alphavantage(t[1])
        insert_daily_data_into_db(1, t[0], av_data)
        if len(av_data) == 0:
            skipped.append(i)
        time.sleep(WAIT_TIME_IN_SECONDS)
        
    print("Successfully added AlphaVantage pricing data to DB.")

