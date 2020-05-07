#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 12:31:36 2020

@author: josephgross
"""


import datetime as dt

import bs4
import requests

import mysql.connector
from mysql.connector import Error



def obtain_parse_wiki_snp500():
    """
    Download \and parse the Wikipedia list of S&P500
    constituents using requests and BeatifulSoup.


    Returns
    -------
    List of tuples
        The list of tuples will be added to the securities master
        database using MySQL

    """

    # Stores the current time, for created_at record (MY_SQL)
    now = dt.datetime.utcnow()
    
    # Use requests and BeautifulSoup to download the 
    # list of S&P500 companies and obtain the symbol table 
    response = requests.get(
        "http://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )
    soup = bs4.BeautifulSoup(response.text, features="lxml")


    # This selects the first table, using CSS Selector syntax
    # and also ignore the header row ([1:])
    symbolsList = soup.select('table')[0].select('tr')[1:]
    
    
    # Obtain the symbol information for each
    # row in the S&P500 consituent table
    symbols = []
    for i, symbol in enumerate(symbolsList):
        tds = symbol.select('td')
        symbols.append(
            (
                tds[0].select('a')[0].text, # Ticker
                'stock', 
                tds[1].select('a')[0].text, # Name
                tds[3].text, # Sector
                'USD', now, now
            )
        )

    return symbols 


def insert_snp500_symbols(symbols):
    """
    Insert the S&P500 symbols into MySQL database

    Parameters
    ----------
    symbols : 'List'
        List of tuples with basic information on S&P500 companies

    Returns
    -------
    None.

    """
    
    column_names = 'ticker, instrument, name, sector, currency, created_date, last_updated_date'
    query = "INSERT INTO symbol({}) " \
            "VALUES(%s,%s,%s,%s,%s,%s,%s)".format(column_names)
 
    try:
        db_host = '127.0.0.1'
        db_user = 'sec_user'
        db_password = 'UZHuYbneFK2'
        db_name = 'securities_master'

        conn = mysql.connector.connect(
                                user=db_user, 
                                password=db_password,
                                host=db_host,
                                database=db_name)
 
        cursor = conn.cursor()
        cursor.executemany(query, symbols)
        
        conn.commit()
        
    except Error as error:
        print(error)
 
    finally:
        cursor.close()
        conn.close()


def truncate_table(table_name):
   
    try:
        db_host = '127.0.0.1'
        db_user = 'sec_user'
        db_password = 'UZHuYbneFK2'
        db_name = 'securities_master'

        connection = mysql.connector.connect(
                                user=db_user, 
                                password=db_password,
                                host=db_host,
                                database=db_name)

        cursor = connection.cursor()
        cursor.execute("TRUNCATE TABLE {}".format(table_name))

        print("{} Table truncated successfully".format(table_name))

    except mysql.connector.Error as error:
        print("Failed to truncate table in MySQL: {}".format(error))
    
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
  
       
# -------------------------------------------------------------------------------------
            
if __name__ == "__main__":
    symbols = (obtain_parse_wiki_snp500())
    
    print(len(symbols))
    
    
    
    #insert_snp500_symbols(symbols)
    #truncate_table('symbol')
    
    for i in range(len(symbols)-1):
       if len(symbols[i]) != len(symbols[i+1]):
           print(i)
